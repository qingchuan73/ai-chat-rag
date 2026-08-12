import os
import hashlib
from datetime import datetime,timedelta  
from dotenv import load_dotenv
from jose import jwt,JWTError
from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

pwd_context = CryptContext(schemes=["bcrypt"])

ALGORITHM="HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def normalize_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def hash_password(password):
    return pwd_context.hash(
        normalize_password(password)
    )

def verify_password(
    password,
    password_hash
):
    normalized_password = normalize_password(password)

    if pwd_context.verify(normalized_password, password_hash):
        return True

    if len(password.encode("utf-8")) <= 72:
        try:
            return pwd_context.verify(
                password,
                password_hash
            )
        except ValueError:
            return False

    return False
    
def create_token(user_id):
    data={
        "user_id":user_id,
        "exp":
            datetime.utcnow()
            +
            timedelta(days=7)
    }
    
    return jwt.encode(
        data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录凭证已失效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
      
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: int = payload.get("user_id") 
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception
