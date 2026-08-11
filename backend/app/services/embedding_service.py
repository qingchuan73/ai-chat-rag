import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-zh")
EMBEDDING_LOCAL_ONLY = os.getenv("EMBEDDING_LOCAL_ONLY", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


@lru_cache(maxsize=1)
def get_embedding_model():
    try:
        return SentenceTransformer(
            EMBEDDING_MODEL_NAME,
            local_files_only=EMBEDDING_LOCAL_ONLY,
        )
    except Exception as exc:
        if EMBEDDING_LOCAL_ONLY:
            raise RuntimeError(
                "Embedding model is not available locally. "
                "Download BAAI/bge-small-zh once, set EMBEDDING_MODEL_NAME to a local model path, "
                "or set EMBEDDING_LOCAL_ONLY=false to allow HuggingFace download."
            ) from exc

        raise


def create_embedding(texts):
    vectors = get_embedding_model().encode(
        texts,
        normalize_embeddings=True
    )

    return vectors.tolist()
