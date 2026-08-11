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
            You maintain long-term conversation memory.
            Merge the old summary and new messages into a concise summary.

            Keep:
            1. User goals
            2. User preferences
            3. Project information
            4. Completed work

            Remove casual small talk.
            """
        },
        {
            "role": "user",
            "content":
            f"""
            Old summary:
            {old_summary or ""}

            New messages:
            {text}
            """
        }
    ]

    result = invoke(
        messages=prompt,
        model_config=model_config
    )

    return result.content
