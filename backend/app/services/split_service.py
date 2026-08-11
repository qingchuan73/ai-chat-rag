CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def split_document(
    text,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
):
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks


def split_document_pages(
    pages,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
):
    chunks = []
    metadatas = []

    for page in pages:
        page_chunks = split_document(
            page.get("content", ""),
            chunk_size,
            chunk_overlap
        )

        for chunk in page_chunks:
            metadatas.append(
                {
                    "page": page.get("page")
                }
            )
            chunks.append(chunk)

    return chunks, metadatas
