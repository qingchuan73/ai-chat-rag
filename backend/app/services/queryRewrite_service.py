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
            You are a query rewriting assistant for vector retrieval.
            Rewrite the current user question into a complete, clear retrieval
            query using the recent conversation.

            Rules:
            1. Preserve the user's real intent.
            2. Resolve pronouns and short follow-ups such as "which page",
               "where did you see that", "source", "original text", and
               "continue".
            3. Add the missing subject, document name, chapter name, or topic
               when it is available in the recent conversation.
            4. Do not answer the question.
            5. Output only the rewritten query.
            6. If the current question is already complete, output it unchanged.
            7. If the current question introduces a new explicit topic, such as
               a chapter name or a feature name, prioritize that new topic and
               do not keep the previous topic unless it is required.
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
