from sqlalchemy.orm import Session

from database.models import KnowledgeFile


def create_knowledge_file(
    db: Session,
    user_id: int,
    original_filename: str,
    storage_filename: str,
    file_type: str,
):
    knowledge_file = KnowledgeFile(
        user_id=user_id,
        original_filename=original_filename,
        storage_filename=storage_filename,
        file_type=file_type,
    )

    db.add(knowledge_file)
    db.commit()
    db.refresh(knowledge_file)

    return knowledge_file


def get_user_knowledge_files(
    db: Session,
    user_id: int,
):
    return (
        db.query(KnowledgeFile)
        .filter(KnowledgeFile.user_id == user_id)
        .order_by(KnowledgeFile.id.desc())
        .all()
    )


def get_user_knowledge_file(
    db: Session,
    user_id: int,
    file_id: int,
):
    return (
        db.query(KnowledgeFile)
        .filter(
            KnowledgeFile.id == file_id,
            KnowledgeFile.user_id == user_id,
        )
        .first()
    )


def get_user_knowledge_file_by_name(
    db: Session,
    user_id: int,
    original_filename: str,
):
    return (
        db.query(KnowledgeFile)
        .filter(
            KnowledgeFile.user_id == user_id,
            KnowledgeFile.original_filename == original_filename,
        )
        .first()
    )


def get_user_knowledge_files_by_ids(
    db: Session,
    user_id: int,
    file_ids: list[int],
):
    if not file_ids:
        return []

    return (
        db.query(KnowledgeFile)
        .filter(
            KnowledgeFile.user_id == user_id,
            KnowledgeFile.id.in_(file_ids),
        )
        .all()
    )


def delete_knowledge_file(
    db: Session,
    knowledge_file: KnowledgeFile,
):
    db.delete(knowledge_file)
    db.commit()
