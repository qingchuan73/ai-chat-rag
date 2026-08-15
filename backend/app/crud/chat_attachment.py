from sqlalchemy.orm import Session

from database.models import ChatAttachment


def create_chat_attachment(
    db: Session,
    user_id: int,
    original_filename: str,
    storage_filename: str,
    file_type: str,
):
    attachment = ChatAttachment(
        user_id=user_id,
        original_filename=original_filename,
        storage_filename=storage_filename,
        file_type=file_type,
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment


def get_user_chat_attachments_by_ids(
    db: Session,
    user_id: int,
    attachment_ids: list[int],
):
    if not attachment_ids:
        return []

    return (
        db.query(ChatAttachment)
        .filter(
            ChatAttachment.user_id == user_id,
            ChatAttachment.id.in_(attachment_ids),
        )
        .all()
    )
