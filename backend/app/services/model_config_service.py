from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from crud.model_config import (
    delete_model_config,
    get_model_config,
    upsert_model_config,
)
from services.crypto_service import decrypt_text, encrypt_text, mask_key


def serialize_model_config(config):
    api_key = decrypt_text(config.api_key_encrypted)

    return {
        "provider": config.provider,
        "base_url": config.base_url,
        "chat_model": config.chat_model,
        "api_key_masked": mask_key(api_key),
        "configured": True,
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
            "provider": "openai",
            "base_url": None,
            "chat_model": "",
            "api_key_masked": "",
            "configured": False,
        }

    return serialize_model_config(config)


def save_user_model_config(
    db: Session,
    user_id: int,
    request,
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

    config = upsert_model_config(
        db=db,
        user_id=user_id,
        provider="openai",
        base_url=request.base_url.strip() or None if request.base_url else None,
        chat_model=request.chat_model.strip(),
        api_key_encrypted=encrypt_text(request.api_key.strip()),
    )

    return serialize_model_config(config)


def delete_user_model_config(
    db: Session,
    user_id: int,
):
    delete_model_config(
        db,
        user_id
    )

    return {
        "message": "Model config deleted"
    }


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
        "provider": config.provider,
        "base_url": config.base_url,
        "chat_model": config.chat_model,
        "api_key": decrypt_text(config.api_key_encrypted),
    }
