from fastapi import APIRouter, Depends, HTTPException, status
from database.database import get_db

from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,    
    MessageResponse     
)

from crud.user import (
    create_user,
    get_user_by_account
)

from services.auth_service import (
    hash_password,
    verify_password,
    create_token
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