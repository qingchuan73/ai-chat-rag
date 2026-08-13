import json

from fastapi import HTTPException

from crud.rag_trace import create_rag_trace
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
from services.ragRouter_service import (
    classify_rag_question_type,
    expand_rag_retrieval_queries,
    should_use_chat_history,
    should_use_knowledge
)
from services.model_config_service import get_runtime_model_config


RAG_LOOKUP_TOP_K = 6
RAG_SYNTHESIS_TOP_K = 18
RAG_SYNTHESIS_QUERY_TOP_K = 8

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
    rag_chunks,
    max_sources=6
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

        if len(sources) >= max_sources:
            break

    return sources


def merge_rag_chunks(chunk_groups, top_k):
    merged = []
    seen = set()

    max_group_length = max(
        (len(group) for group in chunk_groups),
        default=0
    )

    for index in range(max_group_length):
        for group in chunk_groups:
            if index >= len(group):
                continue

            chunk = group[index]
            metadata = chunk.get("metadata", {})
            key = (
                metadata.get("file_id"),
                metadata.get("chunk_index"),
                chunk.get("content")
            )

            if key in seen:
                continue

            seen.add(key)
            merged.append(chunk)

            if len(merged) >= top_k:
                return merged

    return merged


def search_rag_chunks(
    query,
    user_id,
    question_type,
    history,
    model_config
):
    if question_type != "synthesis":
        return (
            search_vectors(
                query=query,
                user_id=user_id,
                top_k=RAG_LOOKUP_TOP_K
            ),
            [query]
        )

    expanded_queries = expand_rag_retrieval_queries(
        question=query,
        history=history,
        model_config=model_config
    )

    chunk_groups = [
        search_vectors(
            query=item,
            user_id=user_id,
            top_k=RAG_SYNTHESIS_QUERY_TOP_K
        )
        for item in expanded_queries
    ]

    return (
        merge_rag_chunks(
            chunk_groups,
            top_k=RAG_SYNTHESIS_TOP_K
        ),
        expanded_queries
    )


def build_rag_context(
    rag_chunks,
    rag_sources
):
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
            来源文件：{source["filename"]}
            切片编号：{source["chunk_index"]}
            页码：{source["page"] or "未提供"}
            相关度：{source["similarity"]}
            内容：
            {item["content"]}
            """
        )

    return "\n\n".join(context_parts)


def build_rag_system_prompt(
    rewritten_query,
    rag_context,
    question_type
):
    if question_type == "synthesis":
        return f"""
        以下知识库上下文与最新用户问题相关。
        你必须只基于这些上下文回答。

        用户当前需要文档级或主题级综合回答。
        请跨页面阅读上下文，把相关证据整合成结构化答案。
        如果多个切片分别描述同一主题的不同侧面，不要只依据单个切片回答。

        要求：
        1. 只回答最新用户问题。
        2. 在上下文支持时，按清晰主题组织答案。
        3. 保留日期、阈值、价格档位、必选/推荐要求、技术名称、页码等具体事实。
        4. 区分“文档明确表述”和“基于文档证据的归纳”。
        5. 除非问题直接询问，否则忽略封面、目录、附录和版本记录。
        6. 如果用户使用的原词没有出现在文档中，但上下文有相邻证据，
           请基于证据归纳最接近的答案，不要直接停在“上下文没有明确说明”。
        7. 如果上下文确实不足，请具体说明缺少什么。
        8. 先给简洁总论，再给支撑要点。
        9. 当上下文存在可支撑的相邻证据时，不要轻易说“资料不足”。
        10. 不要把检索片段当成孤立事实，要连接描述同一战略或目标的相关页面。
        11. 使用事实时，如果有页码，请在回答中标明来源页。
        12. 不要编造来源、页码、章节或引用。

        改写后的检索问题：
        {rewritten_query}

        知识库上下文：
        {rag_context}
        """

    return f"""
    以下知识库上下文可能与当前问题相关。
    当前请求已被路由到知识库，因此你必须只基于这些上下文回答。

    如果上下文没有足够证据回答用户问题，请说明当前知识库上下文没有提供答案。
    不要使用外部知识。

    如果用户询问来源、引用、原文、页码、章节或答案出处，
    只能使用上下文中提供的信息。
    如果上下文没有提供这些元信息，请说明当前知识库上下文未提供。
    不要编造来源、页码、章节或引用。

    使用上下文事实时，如果有页码，请在回答中标明来源页。

    改写后的检索问题：
    {rewritten_query}

    知识库上下文：
    {rag_context}
    """


def build_llm_messages(
    messages,
    latest_question,
    use_history
):
    system_prompt = f"""
    只回答最新用户问题。

    最新用户问题：
    {latest_question}

    除非最新用户问题明确要求，否则不要回答、总结、纠正、继续或复盘更早的问题。
    """

    if use_history:
        llm_messages = list(messages)
    else:
        llm_messages = [
            {
                "role": "user",
                "content": latest_question
            }
        ]

    llm_messages.insert(
        0,
        {
            "role": "system",
            "content": system_prompt
        }
    )

    return llm_messages


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
    expanded_queries = [rewritten_query]
    use_knowledge = should_use_knowledge(
        question=rewritten_query,
        history=history_for_rewrite,
        attachments=getattr(request, "attachments", None),
        model_config=model_config
    )

    rag_question_type = "lookup"

    if not use_knowledge:
        bm25_probe_chunks = search_bm25_vectors(
            query=rewritten_query,
            user_id=user_id,
            top_k=4
        )
        use_knowledge = bool(bm25_probe_chunks)

    if use_knowledge:
        rag_question_type = classify_rag_question_type(
            question=rewritten_query,
            history=history_for_rewrite,
            model_config=model_config
        )

        rag_chunks, expanded_queries = search_rag_chunks(
            query=rewritten_query,
            user_id=user_id,
            question_type=rag_question_type,
            history=history_for_rewrite,
            model_config=model_config
        )

        if not rag_chunks and bm25_probe_chunks:
            rag_chunks = bm25_probe_chunks

    use_chat_history = bool(rag_chunks) or should_use_chat_history(
        question=request.content,
        history=history_for_rewrite,
        model_config=model_config
    )

    rag_sources = build_rag_sources(
        db,
        user_id,
        rag_chunks,
        max_sources=8 if rag_question_type == "synthesis" else 6
    )

    create_rag_trace(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        question=request.content,
        rewritten_query=rewritten_query,
        question_type=rag_question_type,
        used_knowledge=bool(rag_chunks),
        expanded_queries=json.dumps(
            expanded_queries,
            ensure_ascii=False
        ),
        retrieved_count=len(rag_chunks),
        selected_sources=json.dumps(
            rag_sources,
            ensure_ascii=False
        ),
    )

    llm_messages = build_llm_messages(
        messages=messages,
        latest_question=request.content,
        use_history=use_chat_history
    )

    if rag_chunks:
        rag_context = build_rag_context(
            rag_chunks,
            rag_sources
        )

        llm_messages.insert(
            1,
            {
                "role": "system",
                "content": build_rag_system_prompt(
                    rewritten_query=rewritten_query,
                    rag_context=rag_context,
                    question_type=rag_question_type
                )
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
