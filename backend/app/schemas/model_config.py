from pydantic import BaseModel


class ModelConfigRequest(BaseModel):
    api_key: str
    base_url: str | None = None
    chat_model: str


class ModelConfigResponse(BaseModel):
    provider: str
    base_url: str | None = None
    chat_model: str
    api_key_masked: str
    configured: bool
