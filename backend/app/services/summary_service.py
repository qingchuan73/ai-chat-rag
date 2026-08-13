from services.llm_service import invoke


def generate_summary(messages, old_summary=None, model_config=None):
    text = "\n".join([
        f"{m['role']}:{m['content']}"
        for m in messages
    ])

    prompt = [
        {
            "role": "system",
            "content":
            """
            你负责维护长期对话记忆。
            请把旧摘要和新消息合并成一份简洁摘要。

            保留：
            1. 用户目标
            2. 用户偏好
            3. 项目信息
            4. 已完成工作
            5. 重要决策和未解决问题

            删除闲聊和无长期价值的信息。
            """
        },
        {
            "role": "user",
            "content":
            f"""
            旧摘要：
            {old_summary or ""}

            新消息：
            {text}
            """
        }
    ]

    result = invoke(
        messages=prompt,
        model_config=model_config
    )

    return result.content
