import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from crud.chat_attachment import create_chat_attachment


BASE_DIR = Path(__file__).resolve().parents[2]
ATTACHMENT_DIR = BASE_DIR / "chat_attachments"
IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "gif",
}


def ensure_attachment_dir() -> None:
    ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)


def get_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    return suffix or "unknown"


def build_storage_name(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}"


def save_chat_image_attachment(
    db: Session,
    user_id: int,
    file: UploadFile,
) -> dict:
    ensure_attachment_dir()

    original_filename = file.filename or "unknown"
    file_type = get_file_type(original_filename)

    if file_type not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image attachments are allowed",
        )

    storage_name = build_storage_name(original_filename)
    file_path = ATTACHMENT_DIR / storage_name

    with file_path.open("wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)

    attachment = create_chat_attachment(
        db=db,
        user_id=user_id,
        original_filename=original_filename,
        storage_filename=storage_name,
        file_type=file_type,
    )

    return {
        "id": attachment.id,
        "original_filename": attachment.original_filename,
        "storage_filename": attachment.storage_filename,
        "file_type": attachment.file_type,
        "created_at": attachment.created_at,
        "size": file_path.stat().st_size,
        "status": "uploaded",
    }
