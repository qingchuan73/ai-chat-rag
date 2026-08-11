import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from services.document_service import read_document_pages
from services.split_service import split_document_pages
from services.embedding_service import create_embedding
from services.vector_service import delete_vectors_by_file_id, save_vectors

from crud.file import (
    create_knowledge_file,
    delete_knowledge_file,
    get_user_knowledge_file,
    get_user_knowledge_file_by_name,
    get_user_knowledge_files,
)

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {
    "txt",
    "md",
    "markdown",
    "csv",
    "tsv",
    "log",
    "json",
    "yaml",
    "yml",
    "xml",
    "pdf",
    "doc",
    "docx",
    "rtf",
    "html",
    "htm",
    "rst",
}


def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    return suffix or "unknown"


def validate_file_type(filename: str) -> str:
    file_type = get_file_type(filename)
    if file_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only common text and pdf documents are allowed",
        )
    return file_type


def build_storage_name(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}"


def save_uploaded_file(
    db: Session,
    user_id: int,
    file: UploadFile,
) -> dict:
    ensure_upload_dir()

    original_filename = file.filename or "unknown"
    file_type = validate_file_type(original_filename)
    existing_file = get_user_knowledge_file_by_name(
        db,
        user_id,
        original_filename
    )

    if existing_file:
        existing_path = UPLOAD_DIR / existing_file.storage_filename if existing_file.storage_filename else None

        if existing_path and existing_path.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="File already exists in knowledge base",
            )

    storage_name = build_storage_name(original_filename)
    file_path = UPLOAD_DIR / storage_name
    knowledge_file = None

    with file_path.open("wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)

    try:
        knowledge_file = create_knowledge_file(
            db=db,
            user_id=user_id,
            original_filename=original_filename,
            storage_filename=storage_name,
            file_type=file_type,
        )

        pages = read_document_pages(file_path, file_type)

        chunks, chunk_metadatas = split_document_pages(pages)

        vectors = create_embedding(chunks)

        save_vectors(
            chunks=chunks,
            vectors=vectors,
            user_id=user_id,
            file_id=knowledge_file.id,
            chunk_metadatas=chunk_metadatas
        )
    except Exception:
        if knowledge_file:
            delete_vectors_by_file_id(
                user_id=user_id,
                file_id=knowledge_file.id
            )
            delete_knowledge_file(
                db,
                knowledge_file
            )

        if file_path.exists():
            file_path.unlink()

        raise

    return {
        "id": knowledge_file.id,
        "original_filename": knowledge_file.original_filename,
        "storage_filename": knowledge_file.storage_filename,
        "file_type": knowledge_file.file_type,
        "created_at": knowledge_file.created_at,
        "size": file_path.stat().st_size,
        "status": "indexed",
    }


def serialize_knowledge_file(knowledge_file) -> dict:
    storage_filename = knowledge_file.storage_filename
    file_path = UPLOAD_DIR / storage_filename if storage_filename else None
    file_exists = file_path.exists() if file_path else False

    return {
        "id": knowledge_file.id,
        "original_filename": knowledge_file.original_filename,
        "storage_filename": storage_filename,
        "file_type": knowledge_file.file_type,
        "created_at": knowledge_file.created_at,
        "size": file_path.stat().st_size if file_exists else 0,
        "status": "indexed" if file_exists else "missing",
    }


def list_knowledge_files(
    db: Session,
    user_id: int,
) -> dict:
    files = get_user_knowledge_files(
        db,
        user_id
    )

    return {
        "files": [
            serialize_knowledge_file(item)
            for item in files
        ]
    }


def get_knowledge_file_response(
    db: Session,
    user_id: int,
    file_id: int,
):
    knowledge_file = get_user_knowledge_file(
        db,
        user_id,
        file_id
    )

    if not knowledge_file or not knowledge_file.storage_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge file not found",
        )

    file_path = UPLOAD_DIR / knowledge_file.storage_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file is missing",
        )

    return FileResponse(
        path=file_path,
        filename=knowledge_file.original_filename,
        media_type="application/pdf" if knowledge_file.file_type == "pdf" else "application/octet-stream",
    )


def remove_knowledge_file(
    db: Session,
    user_id: int,
    file_id: int,
) -> dict:
    knowledge_file = get_user_knowledge_file(
        db,
        user_id,
        file_id
    )

    if not knowledge_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge file not found",
        )

    delete_vectors_by_file_id(
        user_id=user_id,
        file_id=file_id
    )

    file_path = UPLOAD_DIR / knowledge_file.storage_filename if knowledge_file.storage_filename else None
    if file_path and file_path.exists():
        file_path.unlink()

    delete_knowledge_file(
        db,
        knowledge_file
    )

    return {
        "message": "Knowledge file deleted"
    }


def reindex_knowledge_file(
    db: Session,
    user_id: int,
    file_id: int,
) -> dict:
    knowledge_file = get_user_knowledge_file(
        db,
        user_id,
        file_id
    )

    if not knowledge_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge file not found",
        )

    if not knowledge_file.storage_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file is missing",
        )

    file_path = UPLOAD_DIR / knowledge_file.storage_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file is missing",
        )

    delete_vectors_by_file_id(
        user_id=user_id,
        file_id=file_id
    )

    pages = read_document_pages(
        file_path,
        knowledge_file.file_type
    )
    chunks, chunk_metadatas = split_document_pages(pages)
    vectors = create_embedding(chunks)

    save_vectors(
        chunks=chunks,
        vectors=vectors,
        user_id=user_id,
        file_id=knowledge_file.id,
        chunk_metadatas=chunk_metadatas
    )

    return {
        **serialize_knowledge_file(knowledge_file),
        "status": "indexed",
    }
