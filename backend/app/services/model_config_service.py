from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from crud.model_config import (
    count_model_configs,
    delete_model_config,
    get_model_config,
    get_model_config_by_id,
    list_model_configs,
    set_default_model_config,
    upsert_model_config,
)
from services.crypto_service import decrypt_text, encrypt_text, mask_key


def serialize_model_config(config):
    api_key = decrypt_text(config.api_key_encrypted)

    return {
        "id": config.id,
        "name": config.name,
        "provider": config.provider,
        "base_url": config.base_url,
        "chat_model": config.chat_model,
        "image_model": config.image_model,
        "api_key_masked": mask_key(api_key),
        "configured": True,
        "is_default": config.is_default == "true",
    }


def get_user_model_config_response(
    db: Session,
    user_id: int,
):
    config = get_model_config(
        db,
        user_id
    )

    if not config:
        return {
            "id": None,
            "name": None,
            "provider": "openai",
            "base_url": None,
            "chat_model": "",
            "image_model": None,
            "api_key_masked": "",
            "configured": False,
            "is_default": False,
        }

    return serialize_model_config(config)


def list_user_model_configs(
    db: Session,
    user_id: int,
):
    configs = list_model_configs(
        db,
        user_id
    )

    return {
        "configs": [
            serialize_model_config(config)
            for config in configs
        ]
    }


def save_user_model_config(
    db: Session,
    user_id: int,
    request,
    config_id: int | None = None,
):
    if not request.api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is required",
        )

    if not request.chat_model.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat model is required",
        )

    should_be_current = False
    if config_id:
        old_config = get_model_config_by_id(
            db,
            user_id,
            config_id
        )
        should_be_current = bool(old_config and old_config.is_default == "true")
    else:
        should_be_current = count_model_configs(db, user_id) == 0

    config = upsert_model_config(
        db=db,
        user_id=user_id,
        name=(request.name or request.chat_model).strip(),
        provider="openai",
        base_url=request.base_url.strip() or None if request.base_url else None,
        chat_model=request.chat_model.strip(),
        image_model=request.image_model.strip() or None if request.image_model else None,
        api_key_encrypted=encrypt_text(request.api_key.strip()),
        config_id=config_id,
        is_default=should_be_current,
    )

    return serialize_model_config(config)


def delete_user_model_config(
    db: Session,
    user_id: int,
    config_id: int | None = None,
):
    delete_model_config(
        db,
        user_id,
        config_id
    )

    return {
        "message": "Model config deleted"
    }


def switch_user_default_model_config(
    db: Session,
    user_id: int,
    config_id: int,
):
    config = set_default_model_config(
        db,
        user_id,
        config_id
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model config not found",
        )

    return serialize_model_config(config)


def get_runtime_model_config(
    db: Session,
    user_id: int,
):
    config = get_model_config(
        db,
        user_id
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please configure your model API key first",
        )

    return {
        "id": config.id,
        "name": config.name,
        "provider": config.provider,
        "base_url": config.base_url,
        "chat_model": config.chat_model,
        "image_model": config.image_model,
        "api_key": decrypt_text(config.api_key_encrypted),
    }
