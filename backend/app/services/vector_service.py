import re

import jieba
from rank_bm25 import BM25Okapi

from database.chroma import collection


RAG_SIMILARITY_THRESHOLD = 0.55
BM25_TOP_K_MULTIPLIER = 4
DENSE_TOP_K_MULTIPLIER = 4
LOW_PRIORITY_PENALTY = 0.2
YEAR_MATCH_BOOST = 0.12
BODY_CONTENT_BOOST = 0.08

STOP_WORDS = {
    "当前",
    "内容",
    "方面",
    "还有",
    "这个",
    "那个",
    "什么",
    "为什么",
    "哪些",
    "如何",
    "是否",
    "一下",
    "根据",
    "文档",
    "文件",
    "pdf",
    "PDF",
    "the",
    "and",
    "for",
    "with",
    "from",
}


def save_vectors(
    chunks,
    vectors,
    user_id,
    file_id,
    chunk_metadatas=None
):
    metadatas = []

    for i in range(len(chunks)):
        extra_metadata = chunk_metadatas[i] if chunk_metadatas and i < len(chunk_metadatas) else {}
        metadata = {
            "user_id": user_id,
            "file_id": file_id,
            "chunk_index": i
        }

        for key, value in extra_metadata.items():
            if value is not None:
                metadata[key] = value

        metadatas.append(metadata)

    collection.add(
        ids=[
            f"{file_id}_{i}"
            for i in range(len(chunks))
        ],
        documents=chunks,
        embeddings=vectors,
        metadatas=metadatas
    )


def delete_vectors_by_file_id(
    user_id,
    file_id
):
    collection.delete(
        where={
            "$and": [
                {
                    "user_id": user_id
                },
                {
                    "file_id": file_id
                }
            ]
        }
    )


def tokenize_text(text):
    if not text:
        return []

    tokens = []

    for word in jieba.cut(text):
        token = word.strip()

        if len(token) < 2:
            continue

        if token in STOP_WORDS:
            continue

        tokens.append(token)

    tokens.extend(
        re.findall(
            r"[A-Za-z0-9][A-Za-z0-9\-_/\.]{1,}",
            text
        )
    )

    chinese_blocks = re.findall(
        r"[\u4e00-\u9fff]+",
        text
    )

    for block in chinese_blocks:
        for size in (5, 4, 3, 2):
            if len(block) < size:
                continue

            for index in range(0, len(block) - size + 1):
                token = block[index:index + size]
                if token not in STOP_WORDS:
                    tokens.append(token)

    return tokens


def make_chunk_key(chunk):
    metadata = chunk.get("metadata") or {}
    return (
        metadata.get("file_id"),
        metadata.get("chunk_index"),
        chunk.get("content")
    )


def extract_query_years(query):
    return set(
        re.findall(
            r"(20\d{2}|R1[5-9]|R2[0-9])",
            query or ""
        )
    )


def get_rank_score(chunk, query_years=None):
    metadata = chunk.get("metadata") or {}
    score = float(chunk.get("similarity", 0))
    priority = int(metadata.get("priority") or 1)
    content_type = metadata.get("content_type")
    year_labels = str(metadata.get("year_labels") or "")

    if priority >= 3:
        score -= LOW_PRIORITY_PENALTY

    if content_type == "body":
        score += BODY_CONTENT_BOOST

    if query_years and any(year in year_labels for year in query_years):
        score += YEAR_MATCH_BOOST

    return score


def search_bm25_vectors(
    query,
    user_id,
    top_k=5
):
    result = collection.get(
        where={
            "user_id": user_id
        },
        include=[
            "documents",
            "metadatas",
        ]
    )

    documents = result.get("documents", [])
    metadatas = result.get("metadatas", [])

    if not documents:
        return []

    query_tokens = tokenize_text(query)

    if not query_tokens:
        return []

    tokenized_documents = [
        tokenize_text(document)
        for document in documents
    ]

    bm25 = BM25Okapi(tokenized_documents)
    scores = bm25.get_scores(query_tokens)
    max_score = max(scores) if len(scores) else 0

    if max_score <= 0:
        return []

    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True
    )

    chunks = []

    for index in ranked_indexes[:top_k]:
        score = scores[index]

        if score <= 0:
            continue

        chunks.append(
            {
                "content": documents[index],
                "metadata": metadatas[index],
                "similarity": float(round(score / max_score, 4)),
                "retrieval_type": "bm25",
            }
        )

    return chunks


def search_dense_vectors(
    query,
    user_id,
    top_k,
    similarity_threshold
):
    from services.embedding_service import create_embedding

    query_vector = create_embedding([query])[0]

    result = collection.query(
        query_embeddings=[query_vector],
        n_results=max(top_k * DENSE_TOP_K_MULTIPLIER, 12),
        where={
            "user_id": user_id
        }
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    chunks = []

    for i in range(len(documents)):
        distance = distances[i] if i < len(distances) else 1
        similarity = 1 - distance

        if similarity < similarity_threshold:
            continue

        chunks.append(
            {
                "content": documents[i],
                "metadata": metadatas[i],
                "similarity": float(round(similarity, 4)),
                "retrieval_type": "dense",
            }
        )

    return chunks


def merge_retrieval_results(
    bm25_chunks,
    dense_chunks,
    top_k,
    query=None
):
    merged = []
    seen = set()
    query_years = extract_query_years(query)

    for chunk in bm25_chunks + dense_chunks:
        key = make_chunk_key(chunk)

        if key in seen:
            continue

        seen.add(key)
        merged.append(chunk)

    merged.sort(
        key=lambda chunk: get_rank_score(
            chunk,
            query_years=query_years
        ),
        reverse=True
    )

    return merged[:top_k]


def search_vectors(
    query,
    user_id,
    top_k=5,
    similarity_threshold=RAG_SIMILARITY_THRESHOLD
):
    bm25_chunks = search_bm25_vectors(
        query=query,
        user_id=user_id,
        top_k=top_k * BM25_TOP_K_MULTIPLIER
    )

    dense_chunks = search_dense_vectors(
        query=query,
        user_id=user_id,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )

    return merge_retrieval_results(
        bm25_chunks=bm25_chunks,
        dense_chunks=dense_chunks,
        top_k=top_k,
        query=query
    )
