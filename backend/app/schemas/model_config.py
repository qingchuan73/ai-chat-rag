from pydantic import BaseModel


class ModelConfigRequest(BaseModel):
    api_key: str
    name: str | None = None
    base_url: str | None = None
    chat_model: str
    image_model: str | None = None


class ModelConfigResponse(BaseModel):
    id: int | None = None
    name: str | None = None
    provider: str
    base_url: str | None = None
    chat_model: str
    image_model: str | None = None
    api_key_masked: str
    configured: bool
    is_default: bool = False


class ModelConfigListResponse(BaseModel):
    configs: list[ModelConfigResponse]
