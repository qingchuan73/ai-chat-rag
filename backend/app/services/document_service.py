from pathlib import Path
from pypdf import PdfReader

TEXT_TYPES = {
    "txt", "md", "markdown", "csv", "tsv", "log",
    "json", "yaml", "yml", "xml", "html", "htm", "rst"
}

def read_text(path):
    return Path(path).read_text(
        encoding="utf-8",
        errors="ignore"
    )

def read_pdf(path):
    reader = PdfReader(path)
    texts = []

    for page in reader.pages:
        content = page.extract_text()
        if content:
            texts.append(content)

    return "\n".join(texts)


def read_pdf_pages(path):
    reader = PdfReader(path)
    pages = []

    for index, page in enumerate(reader.pages, start=1):
        content = page.extract_text()
        if content:
            pages.append(
                {
                    "content": content,
                    "page": index
                }
            )

    return pages


def read_document(path, file_type):
    if file_type in TEXT_TYPES:
        return read_text(path)

    if file_type == "pdf":
        return read_pdf(path)

    raise ValueError("Unsupported file type")


def read_document_pages(path, file_type):
    if file_type == "pdf":
        return read_pdf_pages(path)

    return [
        {
            "content": read_document(path, file_type),
            "page": None
        }
    ]
