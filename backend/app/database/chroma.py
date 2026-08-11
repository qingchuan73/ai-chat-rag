import os

import chromadb


client=chromadb.PersistentClient(
    path=os.getenv("CHROMA_PATH", "./chroma")
)


collection=client.get_or_create_collection(
    name="knowledge",
    metadata={
        "hnsw:space":"cosine"
    }
)
