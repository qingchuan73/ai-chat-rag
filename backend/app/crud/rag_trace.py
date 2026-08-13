from database.models import RagTrace


def create_rag_trace(
    db,
    user_id,
    conversation_id,
    question,
    rewritten_query,
    question_type,
    used_knowledge,
    expanded_queries,
    retrieved_count,
    selected_sources,
):
    trace = RagTrace(
        user_id=user_id,
        conversation_id=conversation_id,
        question=question,
        rewritten_query=rewritten_query,
        question_type=question_type,
        used_knowledge="true" if used_knowledge else "false",
        expanded_queries=expanded_queries,
        retrieved_count=retrieved_count,
        selected_sources=selected_sources,
    )

    db.add(trace)
    db.commit()
    db.refresh(trace)

    return trace


def get_user_rag_traces(
    db,
    user_id,
    limit=20,
):
    return (
        db.query(RagTrace)
        .filter(RagTrace.user_id == user_id)
        .order_by(RagTrace.id.desc())
        .limit(limit)
        .all()
    )
