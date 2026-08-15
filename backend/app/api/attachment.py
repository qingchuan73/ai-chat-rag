from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from database.database import get_db
from services.auth_service import get_current_user_id
from services.attachment_service import save_chat_image_attachment


router = APIRouter(
    prefix="/attachment",
    tags=["attachment"],
)


@router.post("/upload")
def upload_attachment(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return save_chat_image_attachment(
        db,
        user_id,
        file
    )
