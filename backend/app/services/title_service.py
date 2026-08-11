from services.llm_service import invoke


def generate_title(content: str, model_config):
    prompt = [
        {
            "role": "user",
            "content":
            f"""
            Generate a short chat title from the user's first message.

            Requirements:
            1. No more than 20 Chinese characters or 8 English words.
            2. Do not add quotes.
            3. Return only the title.

            User message:
            {content}
            """
        }
    ]

    result = invoke(
        messages=prompt,
        model_config=model_config
    )

    return result.content.strip()
