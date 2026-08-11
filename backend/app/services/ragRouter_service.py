from services.llm_service import invoke


def should_use_knowledge(question: str, history=None, attachments=None, model_config=None) -> bool:
    if attachments:
        return True

    if not model_config:
        return False

    prompt = [
        {
            "role": "system",
            "content": """
            You are a RAG intent router.
            Decide whether the user's current question should use the user's
            uploaded knowledge base.

            Reply with only yes or no.

            Return yes when the user is asking about, following up on, or
            trying to verify content that may exist in uploaded private
            documents.

            Return no when the question is ordinary conversation or clearly
            unrelated to uploaded documents.

            Do not rely on a fixed keyword list. Judge by intent and recent
            conversation context.
            """
        },
        {
            "role": "user",
            "content": f"""
            Recent conversation:
            {history or []}

            Current question:
            {question}
            """
        }
    ]

    try:
        result = invoke(
            messages=prompt,
            model_config=model_config
        )
        answer = result.content.strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False
