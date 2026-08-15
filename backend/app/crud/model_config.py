from sqlalchemy.orm import Session

from database.models import UserModelConfig


def list_model_configs(
    db: Session,
    user_id: int,
):
    return (
        db.query(UserModelConfig)
        .filter(UserModelConfig.user_id == user_id)
        .order_by(UserModelConfig.is_default.desc(), UserModelConfig.id.desc())
        .all()
    )


def count_model_configs(
    db: Session,
    user_id: int,
):
    return (
        db.query(UserModelConfig)
        .filter(UserModelConfig.user_id == user_id)
        .count()
    )


def get_model_config(
    db: Session,
    user_id: int,
):
    return (
        db.query(UserModelConfig)
        .filter(UserModelConfig.user_id == user_id)
        .filter(UserModelConfig.is_default == "true")
        .first()
    ) or (
        db.query(UserModelConfig)
        .filter(UserModelConfig.user_id == user_id)
        .first()
    )


def get_model_config_by_id(
    db: Session,
    user_id: int,
    config_id: int,
):
    return (
        db.query(UserModelConfig)
        .filter(UserModelConfig.id == config_id)
        .filter(UserModelConfig.user_id == user_id)
        .first()
    )


def unset_default_model_configs(
    db: Session,
    user_id: int,
):
    (
        db.query(UserModelConfig)
        .filter(UserModelConfig.user_id == user_id)
        .update({"is_default": "false"})
    )


def upsert_model_config(
    db: Session,
    user_id: int,
    name: str,
    provider: str,
    base_url: str | None,
    chat_model: str,
    image_model: str | None,
    api_key_encrypted: str,
    config_id: int | None = None,
    is_default: bool = False,
):
    config = None

    if config_id:
        config = get_model_config_by_id(
            db,
            user_id,
            config_id
        )

    if is_default:
        unset_default_model_configs(
            db,
            user_id
        )

    if config:
        was_current = config.is_default == "true"
        config.name = name
        config.provider = provider
        config.base_url = base_url
        config.chat_model = chat_model
        config.image_model = image_model
        config.api_key_encrypted = api_key_encrypted
        config.is_default = "true" if is_default else ("true" if was_current else "false")
    else:
        config = UserModelConfig(
            user_id=user_id,
            name=name,
            provider=provider,
            base_url=base_url,
            chat_model=chat_model,
            image_model=image_model,
            api_key_encrypted=api_key_encrypted,
            is_default="true" if is_default else "false",
        )
        db.add(config)

    db.commit()
    db.refresh(config)

    return config


def set_default_model_config(
    db: Session,
    user_id: int,
    config_id: int,
):
    config = get_model_config_by_id(
        db,
        user_id,
        config_id
    )

    if not config:
        return None

    unset_default_model_configs(
        db,
        user_id
    )
    config.is_default = "true"
    db.commit()
    db.refresh(config)

    return config


def delete_model_config(
    db: Session,
    user_id: int,
    config_id: int | None = None,
):
    config = (
        get_model_config_by_id(db, user_id, config_id)
        if config_id
        else get_model_config(db, user_id)
    )

    if not config:
        return False

    was_default = config.is_default == "true"
    db.delete(config)
    db.commit()

    if was_default:
        next_config = (
            db.query(UserModelConfig)
            .filter(UserModelConfig.user_id == user_id)
            .order_by(UserModelConfig.id.desc())
            .first()
        )
        if next_config:
            next_config.is_default = "true"
            db.commit()

    return True
