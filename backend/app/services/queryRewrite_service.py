from services.llm_service import invoke


def rewrite_query(
    question: str,
    history: list,
    model_config,
) -> str:
    messages = [
        {
            "role": "system",
            "content": """
            你是用于知识库检索的查询改写助手。
            请结合最近对话，把当前用户问题改写成完整、清晰、适合检索的查询。

            规则：
            1. 保留用户的真实意图。
            2. 处理“第几页”“从哪看到的”“来源”“原文”“继续”“还有呢”等追问。
            3. 如果最近对话中有明确的文档名、章节名、主题或指代对象，请补全到查询中。
            4. 不要回答问题。
            5. 只输出改写后的查询。
            6. 如果当前问题本身已经完整，就原样输出。
            7. 如果当前问题提出了新的明确主题，优先使用新主题，不要无故延续旧主题。
            """
        }
    ]

    for item in history:
        if item.get("role") in ["user", "assistant"]:
            messages.append(
                {
                    "role": item["role"],
                    "content": item["content"]
                }
            )

    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    try:
        response = invoke(
            messages=messages,
            model_config=model_config
        )
        rewritten = response.content.strip()
        return rewritten or question
    except Exception:
        return question
