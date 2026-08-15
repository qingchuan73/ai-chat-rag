import base64
import json
import mimetypes

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
from crud.chat_attachment import get_user_chat_attachments_by_ids
from services.summary_service import generate_summary
from services.title_service import generate_title
from services.llm_service import chat, generate_image, invoke
from services.vector_service import search_bm25_vectors, search_vectors
from services.queryRewrite_service import rewrite_query
from services.ragRouter_service import (
    classify_rag_question_type,
    expand_rag_retrieval_queries,
    should_use_chat_history,
    should_use_knowledge
)
from services.model_config_service import get_runtime_model_config
from services.image_storage_service import save_generated_image
from services.attachment_service import ATTACHMENT_DIR, IMAGE_EXTENSIONS


RAG_LOOKUP_TOP_K = 6
RAG_SYNTHESIS_TOP_K = 18
RAG_SYNTHESIS_QUERY_TOP_K = 8


def get_message_text(content):
    try:
        payload = json.loads(content)
    except Exception:
        return content

    if not isinstance(payload, dict):
        return content

    if payload.get("type") == "image":
        return payload.get("prompt") or ""

    if payload.get("type") == "text":
        return payload.get("content") or ""

    return content


def build_assistant_message_content(content, sources=None):
    if not sources:
        return content

    return json.dumps(
        {
            "type": "text",
            "content": content,
            "sources": sources
        },
        ensure_ascii=False
    )


def build_image_attachment_content(db, user_id, question, attachments):
    if not attachments:
        return None

    file_ids = [
        item.fileId
        for item in attachments
        if getattr(item, "fileId", None)
    ]
    files = get_user_chat_attachments_by_ids(
        db,
        user_id,
        file_ids
    )
    image_files = [
        item
        for item in files
        if item.file_type in IMAGE_EXTENSIONS and item.storage_filename
    ]

    if not image_files:
        return None

    content = [
        {
            "type": "text",
            "text": question or "请分析这张图片。"
        }
    ]

    for image_file in image_files:
        file_path = ATTACHMENT_DIR / image_file.storage_filename
        if not file_path.exists():
            continue

        mime_type = mimetypes.guess_type(str(file_path))[0] or "image/png"
        encoded = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{encoded}"
                }
            }
        )

    return content if len(content) > 1 else None


def should_generate_image(question, model_config):
    prompt = [
        {
            "role": "system",
            "content": """
            你是请求路由器，只判断用户当前请求是否需要生成图片。
            判断为 image 的情况：
            - 用户明确要求画图、生成图片、生成海报、生成插画、生成头像、生成封面、生成 logo、生成壁纸等视觉内容。
            判断为 chat 的情况：
            - 用户只是问问题、分析图片能力、让你解释图片生成原理、让你写提示词、修改代码、普通聊天。
            只输出 image 或 chat。
            """
        },
        {
            "role": "user",
            "content": question
        }
    ]

    try:
        result = invoke(
            messages=prompt,
            model_config=model_config
        )
        return result.content.strip().lower().startswith("image")
    except Exception:
        return False


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


def get_rag_answer_format_prompt():
    return """
    回答必须使用 Markdown，并严格按以下结构组织：

    一、结论
    用 1-2 句话直接回答用户问题。

    二、依据
    列出你实际使用的关键资料依据，并标明页码。
    如果没有页码，说明“当前资料未提供页码”。

    三、展开说明
    按主题分点说明，不要堆砌原文，不要把无关片段硬塞进答案。

    四、不确定性
    如果资料不足、证据不完整或只能做归纳，请明确说明。
    不要编造文档中没有的内容、页码、章节或来源。

    五、可继续追问
    给出 2-3 个用户可以继续追问的方向。
    """


def build_rag_system_prompt(
    rewritten_query,
    rag_context,
    question_type
):
    answer_format = get_rag_answer_format_prompt()

    if question_type == "synthesis":
        return f"""
        以下知识库上下文与最新用户问题相关。
        你必须只基于这些上下文回答。

        用户当前需要文档级或主题级综合回答。
        请跨页面阅读上下文，把相关证据整合成结构化答案。
        如果多个切片分别描述同一主题的不同侧面，不要只依据单个切片回答。

        回答要求：
        1. 只回答最新用户问题。
        2. 在上下文支持时，按清晰主题组织答案。
        3. 保留日期、阈值、价格档位、必选/推荐要求、技术名称、页码等具体事实。
        4. 区分“文档明确表述”和“基于文档证据的归纳”。
        5. 除非问题直接询问，否则忽略封面、目录、附录和版本记录。
        6. 如果用户使用的原词没有出现在文档中，但上下文有相邻证据，
           请基于证据归纳最接近的答案，不要直接停在“上下文没有明确说明”。
        7. 如果上下文确实不足，请具体说明缺少什么。
        8. 不要把检索片段当成孤立事实，要连接描述同一战略或目标的相关页面。
        9. 使用事实时，如果有页码，请在回答中标明来源页。
        10. 不要编造来源、页码、章节或引用。

        {answer_format}

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

    {answer_format}

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

    if should_generate_image(request.content, model_config):
        create_message(
            db,
            conversation_id,
            "user",
            request.content
        )

        yield f"data: {json.dumps({'type': 'image_start'}, ensure_ascii=False)}\n\n"

        if not model_config.get("image_model"):
            error_message = "图片生成失败：请先在系统设置中为当前模型配置生图模型。"
            create_message(
                db,
                conversation_id,
                "assistant",
                error_message
            )
            yield f"data: {json.dumps({'content': error_message}, ensure_ascii=False)}\n\n"
            return

        try:
            raw_image_url = generate_image(
                request.content,
                model_config
            )
            image_url = save_generated_image(raw_image_url)
        except Exception as error:
            error_detail = str(error)
            if len(error_detail) > 300:
                error_detail = f"{error_detail[:300]}..."
            error_message = (
                "图片生成失败：当前模型不能用于图片生成。"
                "请检查生图模型是否支持 images/generations。"
                f"\n\n错误详情：{error_detail}"
            )
            create_message(
                db,
                conversation_id,
                "assistant",
                error_message
            )
            yield f"data: {json.dumps({'content': error_message}, ensure_ascii=False)}\n\n"
            return

        image_message = {
            "type": "image",
            "url": image_url,
            "prompt": request.content
        }

        create_message(
            db,
            conversation_id,
            "assistant",
            json.dumps(image_message, ensure_ascii=False)
        )

        yield f"data: {json.dumps({'type': 'image', 'image': image_message}, ensure_ascii=False)}\n\n"
        return

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
                "content": get_message_text(m.content)
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

    image_content = build_image_attachment_content(
        db,
        user_id,
        request.content,
        getattr(request, "attachments", None)
    )

    if image_content:
        llm_messages = build_llm_messages(
            messages=messages,
            latest_question=request.content,
            use_history=True
        )

        for message in reversed(llm_messages):
            if message["role"] == "user":
                message["content"] = image_content
                break
        ai_content = []

        try:
            for chunk in chat(llm_messages, model_config):
                ai_content.append(chunk)
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception:
            error_message = "识图失败：当前模型可能不支持图片输入，请切换到支持多模态视觉的聊天模型。"
            ai_content = [error_message]
            yield f"data: {json.dumps({'content': error_message}, ensure_ascii=False)}\n\n"

        finish_content = "".join(ai_content)
        messages.append(
            {
                "role": "assistant",
                "content": finish_content
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
        return

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

    try:
        for chunk in chat(llm_messages, model_config):
            ai_content.append(chunk)

            yield f"data: {json.dumps({'content': chunk})}\n\n"
    except Exception:
        error_message = (
            "模型调用失败：当前模型不支持本次请求使用的接口。"
            "如果这是聊天问题，请切换到聊天模型；如果是图片生成，请切换到支持 images/generations 的图片模型。"
        )
        ai_content = [error_message]
        yield f"data: {json.dumps({'content': error_message}, ensure_ascii=False)}\n\n"

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

        try:
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
        except Exception:
            summary = old_summary or ""

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
        build_assistant_message_content(
            finish_content,
            rag_sources
        )
    )

    count = get_message_count(
        db,
        conversation_id,
        user_id
    )

    if count == 2:
        try:
            title = generate_title(
                request.content,
                model_config=model_config
            )

            update_title(
                db,
                conversation_id,
                title
            )
        except Exception:
            pass
