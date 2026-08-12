from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username:str
    account:str
    password:str


class LoginRequest(BaseModel):
    account:str
    password:str
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    
class MessageResponse(BaseModel):
    message: str
