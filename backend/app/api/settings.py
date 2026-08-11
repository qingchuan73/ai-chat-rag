from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from schemas.model_config import ModelConfigRequest, ModelConfigResponse
from services.auth_service import get_current_user_id
from services.model_config_service import (
    delete_user_model_config,
    get_user_model_config_response,
    save_user_model_config,
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


@router.delete("/model")
def delete_model_config(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return delete_user_model_config(
        db,
        user_id
    )
