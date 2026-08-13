from fastapi import APIRouter, Depends, HTTPException, status
from database.database import get_db

from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,    
    MessageResponse,
    UserInfoResponse
)

from crud.user import (
    create_user,
    get_user_by_account,
    get_user_by_id
)

from services.auth_service import (
    hash_password,
    verify_password,
    create_token,
    get_current_user_id
)

router = APIRouter(
    prefix='/auth',
    tags=["auth"]
)

@router.post(
    "/register", 
    status_code=status.HTTP_201_CREATED, 
    response_model=MessageResponse
)
def register(
    request: RegisterRequest,
    db=Depends(get_db)
):
    exist = get_user_by_account(db, request.account)
    
    if exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号已经存在"
        )
        
    create_user(
        db,
        request.username,
        request.account,
        hash_password(request.password)
    )
    
    return {"message": "注册成功"}
    


@router.post(
    "/login", 
    response_model=TokenResponse
)
def login(
    request: LoginRequest,
    db=Depends(get_db)
):
    user = get_user_by_account(db, request.account)
    
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误"
        )
        
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误"
        )
        
    token = create_token(user.id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username
    }


@router.get(
    "/me",
    response_model=UserInfoResponse
)
def get_current_user(
    db=Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    user = get_user_by_id(
        db,
        user_id
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return {
        "id": user.id,
        "username": user.username,
        "account": user.account
    }
