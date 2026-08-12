from pydantic import BaseModel, field_validator


def validate_bcrypt_password(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("password must be at most 72 bytes")

    return value

class RegisterRequest(BaseModel):
    username:str
    account:str
    password:str

    @field_validator("password")
    @classmethod
    def password_length_must_fit_bcrypt(cls, value: str) -> str:
        return validate_bcrypt_password(value)


class LoginRequest(BaseModel):
    account:str
    password:str

    @field_validator("password")
    @classmethod
    def password_length_must_fit_bcrypt(cls, value: str) -> str:
        return validate_bcrypt_password(value)
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    
class MessageResponse(BaseModel):
    message: str
