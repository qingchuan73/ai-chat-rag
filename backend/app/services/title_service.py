from services.llm_service import invoke


def generate_title(content: str, model_config):
    prompt = [
        {
            "role": "user",
            "content":
            f"""
            请根据用户第一条消息生成一个简短会话标题。

            要求：
            1. 不超过 20 个中文字符或 8 个英文单词。
            2. 不要加引号。
            3. 只返回标题，不要解释。

            用户消息：
            {content}
            """
        }
    ]

    result = invoke(
        messages=prompt,
        model_config=model_config
    )

    return result.content.strip()
