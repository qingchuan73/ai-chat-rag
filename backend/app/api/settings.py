from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from schemas.model_config import (
    ModelConfigListResponse,
    ModelConfigRequest,
    ModelConfigResponse,
)
from services.auth_service import get_current_user_id
from services.model_config_service import (
    delete_user_model_config,
    get_user_model_config_response,
    list_user_model_configs,
    save_user_model_config,
    switch_user_default_model_config,
)


router = APIRouter(
    prefix="/settings",
    tags=["settings"],
)


@router.get("/model", response_model=ModelConfigResponse)
def get_model_config(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return get_user_model_config_response(
        db,
        user_id
    )


@router.get("/models", response_model=ModelConfigListResponse)
def list_model_config(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return list_user_model_configs(
        db,
        user_id
    )


@router.post("/model", response_model=ModelConfigResponse)
def save_model_config(
    request: ModelConfigRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return save_user_model_config(
        db,
        user_id,
        request
    )


@router.put("/model/{config_id}", response_model=ModelConfigResponse)
def update_model_config(
    config_id: int,
    request: ModelConfigRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return save_user_model_config(
        db,
        user_id,
        request,
        config_id
    )


@router.post("/model/{config_id}/default", response_model=ModelConfigResponse)
def set_default_model_config(
    config_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return switch_user_default_model_config(
        db,
        user_id,
        config_id
    )


@router.delete("/model")
def delete_model_config(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return delete_user_model_config(
        db,
        user_id
    )


@router.delete("/model/{config_id}")
def delete_model_config_by_id(
    config_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return delete_user_model_config(
        db,
        user_id,
        config_id
    )
