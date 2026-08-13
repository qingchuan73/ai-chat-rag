import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud.rag_trace import get_user_rag_traces
from database.database import get_db
from services.auth_service import get_current_user_id


router = APIRouter(
    prefix="/rag-trace",
    tags=["rag-trace"],
)


def parse_json_field(value, fallback):
    if not value:
        return fallback

    try:
        return json.loads(value)
    except Exception:
        return fallback


def build_trace_prediction(trace, selected_sources):
    if trace.used_knowledge != "true":
        return {
            "level": "normal",
            "reason": "Question was not routed to the knowledge base."
        }

    if not trace.retrieved_count:
        return {
            "level": "weak",
            "reason": "No knowledge chunks were retrieved."
        }

    similarities = [
        float(source.get("similarity") or 0)
        for source in selected_sources
        if isinstance(source, dict)
    ]
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0

    if trace.retrieved_count >= 5 and avg_similarity >= 0.65:
        return {
            "level": "good",
            "reason": "Enough chunks were retrieved with solid average relevance."
        }

    if trace.retrieved_count >= 3:
        return {
            "level": "medium",
            "reason": "Some evidence was retrieved, but relevance or coverage may be limited."
        }

    return {
        "level": "weak",
        "reason": "Retrieved evidence is sparse, so the answer may be incomplete."
    }


@router.get("")
def list_rag_traces(
    limit: int = 20,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    traces = get_user_rag_traces(
        db=db,
        user_id=user_id,
        limit=min(max(limit, 1), 100),
    )

    items = []

    for trace in traces:
        selected_sources = parse_json_field(
            trace.selected_sources,
            []
        )

        items.append(
            {
                "id": trace.id,
                "conversation_id": trace.conversation_id,
                "question": trace.question,
                "rewritten_query": trace.rewritten_query,
                "question_type": trace.question_type,
                "used_knowledge": trace.used_knowledge == "true",
                "expanded_queries": parse_json_field(trace.expanded_queries, []),
                "retrieved_count": trace.retrieved_count,
                "selected_sources": selected_sources,
                "prediction": build_trace_prediction(
                    trace,
                    selected_sources
                ),
                "created_at": trace.created_at,
            }
        )

    return {
        "traces": items
    }
