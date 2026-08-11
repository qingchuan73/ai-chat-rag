from fastapi import APIRouter,Depends

from schemas.chat import ChatRequest
from services.llm_service import chat
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session
from database.database import get_db
from services.chat_service import chat_stream_service
from services.auth_service import get_current_user_id 
from services.model_config_service import get_runtime_model_config

router=APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("")
def chat_endpoint(request:ChatRequest,db:Session=Depends(get_db),user_id:int = Depends(get_current_user_id)):
    print(request)
    conversation_id = request.conversation_id
    model_config = get_runtime_model_config(
        db,
        user_id
    )
    return StreamingResponse(
        chat_stream_service(
            request,
            db,
            user_id,
            model_config
            
        ),
        media_type="text/event-stream"
    )
