from services.llm_service import invoke


def _compact_history(history: list) -> list:
    compacted = []

    for item in history[-4:]:
        role = item.get("role")
        if role not in ["user", "assistant"]:
            continue

        content = " ".join(str(item.get("content", "")).split())
        if not content:
            continue

        max_length = 160 if role == "user" else 220
        compacted.append(
            {
                "role": role,
                "content": content[:max_length]
            }
        )

    return compacted


def _clean_rewritten_query(text: str, fallback: str) -> str:
    rewritten = text.strip()

    for prefix in ["改写：", "改写:", "查询：", "查询:", "检索问题：", "检索问题:"]:
        if rewritten.startswith(prefix):
            rewritten = rewritten[len(prefix):].strip()

    return rewritten or fallback


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
            请只围绕“当前用户最后一句问题”生成一个完整、清晰、适合检索的查询。

            规则：
            1. 保留用户的真实意图。
            2. 历史对话只能用于补全省略的主语、文件名、章节名、疾病名、产品名或指代对象。
            3. 不要把历史中已经问过的问题合并进新查询。
            4. 如果当前问题只问“药物/用药/吃什么药”，改写结果只能聚焦药物，不要加入病因、诊断或整体治疗方法。
            5. 如果当前问题只问“原因/为什么”，改写结果只能聚焦原因，不要加入上一轮答案里的所有结论。
            6. 如果当前问题只问“第几页”“来源”“原文”，改写结果只补全要追溯的对象。
            7. 如果当前问题本身已经完整，就原样输出。
            8. 如果当前问题提出了新的明确主题，优先使用新主题，不要无故延续旧主题。
            9. 不要回答问题。
            10. 只输出一条改写后的查询，不要解释，不要编号。

            示例：
            历史：用户问“中国肺动脉高压的病因是什么”，又问“如何治疗呢”
            当前问题：要吃什么药物
            正确输出：根据当前文件，中国肺动脉高压治疗涉及哪些药物？
            错误输出：根据当前文件，中国肺动脉高压的病因、治疗方法和用药是什么？
            """
        }
    ]

    for item in _compact_history(history):
        messages.append(item)

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
        return _clean_rewritten_query(response.content, question)
    except Exception:
        return question
