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
            浣犳槸璇锋眰璺敱鍣紝鍙垽鏂敤鎴峰綋鍓嶈姹傛槸鍚﹂渶瑕佺敓鎴愬浘鐗囥€?
            鍒ゆ柇涓?image 鐨勬儏鍐碉細
            - 鐢ㄦ埛鏄庣‘瑕佹眰鐢诲浘銆佺敓鎴愬浘鐗囥€佺敓鎴愭捣鎶ャ€佺敓鎴愭彃鐢汇€佺敓鎴愬ご鍍忋€佺敓鎴愬皝闈€佺敓鎴?logo銆佺敓鎴愬绾哥瓑瑙嗚鍐呭銆?
            鍒ゆ柇涓?chat 鐨勬儏鍐碉細
            - 鐢ㄦ埛鍙槸闂棶棰樸€佸垎鏋愬浘鐗囪兘鍔涖€佽浣犺В閲婂浘鐗囩敓鎴愬師鐞嗐€佽浣犲啓鎻愮ず璇嶃€佷慨鏀逛唬鐮併€佹櫘閫氳亰澶┿€?
            鍙緭鍑?image 鎴?chat銆?            """
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
    鍥炵瓟蹇呴』浣跨敤 Markdown锛屽苟涓ユ牸鎸変互涓嬬粨鏋勭粍缁囷細

    涓€銆佺粨璁?
    鐢?1-2 鍙ヨ瘽鐩存帴鍥炵瓟鐢ㄦ埛闂銆?

    浜屻€佷緷鎹?
    鍒楀嚭浣犲疄闄呬娇鐢ㄧ殑鍏抽敭璧勬枡渚濇嵁锛屽苟鏍囨槑椤电爜銆?
    濡傛灉娌℃湁椤电爜锛岃鏄庘€滃綋鍓嶈祫鏂欐湭鎻愪緵椤电爜鈥濄€?

    涓夈€佸睍寮€璇存槑
    鎸変富棰樺垎鐐硅鏄庯紝涓嶈鍫嗙爩鍘熸枃锛屼笉瑕佹妸鏃犲叧鐗囨纭杩涚瓟妗堛€?

    鍥涖€佷笉纭畾鎬?
    濡傛灉璧勬枡涓嶈冻銆佽瘉鎹笉瀹屾暣鎴栧彧鑳藉仛褰掔撼锛岃鏄庣‘璇存槑銆?
    涓嶈缂栭€犳枃妗ｄ腑娌℃湁鐨勫唴瀹广€侀〉鐮併€佺珷鑺傛垨鏉ユ簮銆?

    浜斻€佸彲缁х画杩介棶
    缁欏嚭 2-3 涓敤鎴峰彲浠ョ户缁拷闂殑鏂瑰悜銆?
    """


def build_rag_system_prompt(
    rewritten_query,
    rag_context,
    question_type
):
    answer_format = get_rag_answer_format_prompt()

    if question_type == "synthesis":
        return f"""
        浠ヤ笅鐭ヨ瘑搴撲笂涓嬫枃涓庢渶鏂扮敤鎴烽棶棰樼浉鍏炽€?
        浣犲繀椤诲彧鍩轰簬杩欎簺涓婁笅鏂囧洖绛斻€?

        鐢ㄦ埛褰撳墠闇€瑕佹枃妗ｇ骇鎴栦富棰樼骇缁煎悎鍥炵瓟銆?
        璇疯法椤甸潰闃呰涓婁笅鏂囷紝鎶婄浉鍏宠瘉鎹暣鍚堟垚缁撴瀯鍖栫瓟妗堛€?
        濡傛灉澶氫釜鍒囩墖鍒嗗埆鎻忚堪鍚屼竴涓婚鐨勪笉鍚屼晶闈紝涓嶈鍙緷鎹崟涓垏鐗囧洖绛斻€?

        鍥炵瓟瑕佹眰锛?
        1. 鍙洖绛旀渶鏂扮敤鎴烽棶棰樸€?
        2. 鍦ㄤ笂涓嬫枃鏀寔鏃讹紝鎸夋竻鏅颁富棰樼粍缁囩瓟妗堛€?
        3. 淇濈暀鏃ユ湡銆侀槇鍊笺€佷环鏍兼。浣嶃€佸繀閫?鎺ㄨ崘瑕佹眰銆佹妧鏈悕绉般€侀〉鐮佺瓑鍏蜂綋浜嬪疄銆?
        4. 鍖哄垎鈥滄枃妗ｆ槑纭〃杩扳€濆拰鈥滃熀浜庢枃妗ｈ瘉鎹殑褰掔撼鈥濄€?
        5. 闄ら潪闂鐩存帴璇㈤棶锛屽惁鍒欏拷鐣ュ皝闈€佺洰褰曘€侀檮褰曞拰鐗堟湰璁板綍銆?
        6. 濡傛灉鐢ㄦ埛浣跨敤鐨勫師璇嶆病鏈夊嚭鐜板湪鏂囨。涓紝浣嗕笂涓嬫枃鏈夌浉閭昏瘉鎹紝
           璇峰熀浜庤瘉鎹綊绾虫渶鎺ヨ繎鐨勭瓟妗堬紝涓嶈鐩存帴鍋滃湪鈥滀笂涓嬫枃娌℃湁鏄庣‘璇存槑鈥濄€?
        7. 濡傛灉涓婁笅鏂囩‘瀹炰笉瓒筹紝璇峰叿浣撹鏄庣己灏戜粈涔堛€?
        8. 涓嶈鎶婃绱㈢墖娈靛綋鎴愬绔嬩簨瀹烇紝瑕佽繛鎺ユ弿杩板悓涓€鎴樼暐鎴栫洰鏍囩殑鐩稿叧椤甸潰銆?
        9. 浣跨敤浜嬪疄鏃讹紝濡傛灉鏈夐〉鐮侊紝璇峰湪鍥炵瓟涓爣鏄庢潵婧愰〉銆?
        10. 涓嶈缂栭€犳潵婧愩€侀〉鐮併€佺珷鑺傛垨寮曠敤銆?

        {answer_format}

        鏀瑰啓鍚庣殑妫€绱㈤棶棰橈細
        {rewritten_query}

        鐭ヨ瘑搴撲笂涓嬫枃锛?
        {rag_context}
        """

    return f"""
    浠ヤ笅鐭ヨ瘑搴撲笂涓嬫枃鍙兘涓庡綋鍓嶉棶棰樼浉鍏炽€?
    褰撳墠璇锋眰宸茶璺敱鍒扮煡璇嗗簱锛屽洜姝や綘蹇呴』鍙熀浜庤繖浜涗笂涓嬫枃鍥炵瓟銆?

    濡傛灉涓婁笅鏂囨病鏈夎冻澶熻瘉鎹洖绛旂敤鎴烽棶棰橈紝璇疯鏄庡綋鍓嶇煡璇嗗簱涓婁笅鏂囨病鏈夋彁渚涚瓟妗堛€?
    涓嶈浣跨敤澶栭儴鐭ヨ瘑銆?

    濡傛灉鐢ㄦ埛璇㈤棶鏉ユ簮銆佸紩鐢ㄣ€佸師鏂囥€侀〉鐮併€佺珷鑺傛垨绛旀鍑哄锛?
    鍙兘浣跨敤涓婁笅鏂囦腑鎻愪緵鐨勪俊鎭€?
    濡傛灉涓婁笅鏂囨病鏈夋彁渚涜繖浜涘厓淇℃伅锛岃璇存槑褰撳墠鐭ヨ瘑搴撲笂涓嬫枃鏈彁渚涖€?
    涓嶈缂栭€犳潵婧愩€侀〉鐮併€佺珷鑺傛垨寮曠敤銆?

    浣跨敤涓婁笅鏂囦簨瀹炴椂锛屽鏋滄湁椤电爜锛岃鍦ㄥ洖绛斾腑鏍囨槑鏉ユ簮椤点€?

    {answer_format}

    鏀瑰啓鍚庣殑妫€绱㈤棶棰橈細
    {rewritten_query}

    鐭ヨ瘑搴撲笂涓嬫枃锛?
    {rag_context}
    """

def build_llm_messages(
    messages,
    latest_question,
    use_history
):
    system_prompt = f"""
    鍙洖绛旀渶鏂扮敤鎴烽棶棰樸€?

    鏈€鏂扮敤鎴烽棶棰橈細
    {latest_question}

    闄ら潪鏈€鏂扮敤鎴烽棶棰樻槑纭姹傦紝鍚﹀垯涓嶈鍥炵瓟銆佹€荤粨銆佺籂姝ｃ€佺户缁垨澶嶇洏鏇存棭鐨勯棶棰樸€?
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
        finish_content
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
