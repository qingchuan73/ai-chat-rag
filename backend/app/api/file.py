from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from database.database import get_db
from services.auth_service import get_current_user_id
from services.file_service import (
    get_knowledge_file_response,
    list_knowledge_files,
    reindex_knowledge_file,
    remove_knowledge_file,
    save_uploaded_file,
)

router = APIRouter(
    prefix="/file",
    tags=["file"],
)


@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return save_uploaded_file(db, user_id, file)


@router.get("")
def list_files(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return list_knowledge_files(db, user_id)


@router.get("/{file_id}/preview")
def preview_file(
    file_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return get_knowledge_file_response(db, user_id, file_id)


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return remove_knowledge_file(db, user_id, file_id)


@router.post("/{file_id}/reindex")
def reindex_file(
    file_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return reindex_knowledge_file(db, user_id, file_id)
