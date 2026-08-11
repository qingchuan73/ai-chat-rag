from sqlalchemy.orm import Session

from database.models import UserModelConfig


def get_model_config(
    db: Session,
    user_id: int,
):
    return (
        db.query(UserModelConfig)
        .filter(UserModelConfig.user_id == user_id)
        .first()
    )


def upsert_model_config(
    db: Session,
    user_id: int,
    provider: str,
    base_url: str | None,
    chat_model: str,
    api_key_encrypted: str,
):
    config = get_model_config(
        db,
        user_id
    )

    if config:
        config.provider = provider
        config.base_url = base_url
        config.chat_model = chat_model
        config.api_key_encrypted = api_key_encrypted
    else:
        config = UserModelConfig(
            user_id=user_id,
            provider=provider,
            base_url=base_url,
            chat_model=chat_model,
            api_key_encrypted=api_key_encrypted,
        )
        db.add(config)

    db.commit()
    db.refresh(config)

    return config


def delete_model_config(
    db: Session,
    user_id: int,
):
    config = get_model_config(
        db,
        user_id
    )

    if not config:
        return False

    db.delete(config)
    db.commit()

    return True
