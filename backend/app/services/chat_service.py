import json

from fastapi import HTTPException

from crud.message import (
    create_message,
    update_message,
    get_conversation_messages,
    get_message_count
)
from redisUtils.context_cache import (
    get_context,
    save_context
)
from crud.conversation import (
    update_title,
    update_summary,
    get_summary,
    get_user_conversation
)
from crud.file import get_user_knowledge_files_by_ids
from services.summary_service import generate_summary
from services.title_service import generate_title
from services.llm_service import chat
from services.vector_service import search_bm25_vectors, search_vectors
from services.queryRewrite_service import rewrite_query
from services.ragRouter_service import should_use_knowledge
from services.model_config_service import get_runtime_model_config


def save_user_message(
    db,
    conversation_id,
    content
):
    return create_message(
        db,
        conversation_id,
        "user",
        content
    )


def create_ai_message(
    db,
    conversation_id
):
    return create_message(
        db,
        conversation_id,
        "assistant",
        ""
    )


def finish_ai_message(
    db,
    message_id,
    content
):
    return update_message(
        db,
        message_id,
        content
    )


def build_rag_sources(
    db,
    user_id,
    rag_chunks
):
    file_ids = list({
        item.get("metadata", {}).get("file_id")
        for item in rag_chunks
        if item.get("metadata", {}).get("file_id")
    })

    files = get_user_knowledge_files_by_ids(
        db,
        user_id,
        file_ids
    )
    file_map = {
        item.id: item
        for item in files
    }

    sources = []
    seen = set()

    for item in rag_chunks:
        metadata = item.get("metadata", {})
        file_id = metadata.get("file_id")
        knowledge_file = file_map.get(file_id)
        filename = knowledge_file.original_filename if knowledge_file else "Unknown file"
        page = metadata.get("page")
        source_key = (filename, page) if page else (filename, metadata.get("chunk_index"))

        if source_key in seen:
            continue

        seen.add(source_key)

        sources.append(
            {
                "file_id": file_id,
                "filename": filename,
                "file_type": knowledge_file.file_type if knowledge_file else None,
                "chunk_index": metadata.get("chunk_index"),
                "page": page,
                "similarity": round(item.get("similarity", 0), 4),
            }
        )

    return sources


def chat_stream_service(
    request,
    db,
    user_id,
    model_config=None
):
    conversation_id = request.conversation_id
    if model_config is None:
        model_config = get_runtime_model_config(
            db,
            user_id
        )

    conversation = get_user_conversation(
        db,
        conversation_id,
        user_id
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    messages = get_context(
        user_id,
        conversation_id
    )

    if not messages:
        summary = get_summary(
            db,
            conversation_id
        )
        history = get_conversation_messages(
            db,
            conversation_id,
            user_id,
            limit=20
        )

        messages = [
            {
                "role": m.role,
                "content": m.content
            }
            for m in history
        ]

        if summary:
            messages.insert(
                0,
                {
                    "role": "system",
                    "content":
                    f"""
                    Previous conversation summary:
                    {summary}
                    """
                }
            )

    user_message = {
        "role": "user",
        "content": request.content
    }

    messages.append(user_message)

    create_message(
        db,
        conversation_id,
        "user",
        request.content
    )

    save_context(
        user_id,
        conversation_id,
        messages
    )

    history_for_rewrite = [
        m for m in messages[:-1][-6:]
        if m["role"] in ["user", "assistant"]
    ]

    rewritten_query = rewrite_query(
        question=request.content,
        history=history_for_rewrite,
        model_config=model_config
    )

    rag_chunks = []
    bm25_probe_chunks = []
    use_knowledge = should_use_knowledge(
        question=rewritten_query,
        history=history_for_rewrite,
        attachments=getattr(request, "attachments", None),
        model_config=model_config
    )

    if not use_knowledge:
        bm25_probe_chunks = search_bm25_vectors(
            query=rewritten_query,
            user_id=user_id,
            top_k=3
        )
        use_knowledge = bool(bm25_probe_chunks)

    if use_knowledge:
        rag_chunks = search_vectors(
            query=rewritten_query,
            user_id=user_id,
            top_k=5
        )

        if not rag_chunks and bm25_probe_chunks:
            rag_chunks = bm25_probe_chunks

    rag_sources = build_rag_sources(
        db,
        user_id,
        rag_chunks
    )

    llm_messages = list(messages)

    llm_messages.insert(
        0,
        {
            "role": "system",
            "content":
            """
            Answer only the latest user question.
            Use previous messages only to understand context, references, and
            omitted details. Do not repeat answers to previous questions.
            """
        }
    )

    if rag_chunks:
        context_parts = []

        for item in rag_chunks:
            metadata = item.get("metadata", {})
            page = metadata.get("page")
            chunk_index = metadata.get("chunk_index")
            file_id = metadata.get("file_id")
            source = next(
                (
                    candidate
                    for candidate in rag_sources
                    if candidate.get("file_id") == file_id
                    and (
                        candidate.get("page") == page
                        if page
                        else candidate.get("chunk_index") == chunk_index
                    )
                ),
                {
                    "filename": "Unknown file",
                    "chunk_index": chunk_index,
                    "page": page,
                    "similarity": round(item.get("similarity", 0), 4),
                }
            )
            context_parts.append(
                f"""
                Source file: {source["filename"]}
                Chunk index: {source["chunk_index"]}
                Page: {source["page"] or "not provided"}
                Similarity: {source["similarity"]}
                Content:
                {item["content"]}
                """
            )

        rag_context = "\n\n".join(context_parts)

        llm_messages.insert(
            1,
            {
                "role": "system",
                "content":
                f"""
                The following knowledge base context may be relevant.
                Because the current request was routed to the knowledge base,
                you must answer only from this context.

                If the context does not contain enough evidence for the user's
                question, say that the current knowledge base context does not
                provide the answer. Do not use outside knowledge.

                If the user asks for source, citation, original text, page
                number, chapter, or where an answer came from, only use
                information present in this context. If the context does not
                provide that metadata, say that the current knowledge base
                context does not provide it. Do not invent sources, pages,
                chapters, or citations.

                When you use a fact from the context, mention the source page
                in the answer if the page is provided.

                Rewritten retrieval query:
                {rewritten_query}

                Knowledge base context:
                {rag_context}
                """
            }
        )

    ai_content = []

    if rag_sources:
        yield f"data: {json.dumps({'sources': rag_sources})}\n\n"

    for chunk in chat(llm_messages, model_config):
        ai_content.append(chunk)

        yield f"data: {json.dumps({'content': chunk})}\n\n"

    finish_content = "".join(ai_content)

    messages.append(
        {
            "role": "assistant",
            "content": finish_content
        }
    )

    if len(messages) > 41:
        old_messages = [
            m for m in messages[:-20]
            if m["role"] != "system"
        ]

        old_summary = get_summary(
            db,
            conversation_id
        )

        summary = generate_summary(
            old_messages,
            old_summary,
            model_config=model_config
        )

        update_summary(
            db,
            conversation_id,
            summary
        )

        messages = messages[-20:]

        messages.insert(
            0,
            {
                "role": "system",
                "content":
                f"""
                Previous conversation summary:
                {summary}
                """
            }
        )

        save_context(
            user_id,
            conversation_id,
            messages
        )

    create_message(
        db,
        request.conversation_id,
        "assistant",
        finish_content
    )

    count = get_message_count(
        db,
        conversation_id,
        user_id
    )

    if count == 2:
        title = generate_title(
            request.content,
            model_config=model_config
        )

        update_title(
            db,
            conversation_id,
            title
        )
