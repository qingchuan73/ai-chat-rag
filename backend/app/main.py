import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from api.chat import router
from api.file import router as file_router

from fastapi.middleware.cors import CORSMiddleware
from api.conversation import router as conversation_router
from api.auth import router as auth_router
from api.settings import router as settings_router



app = FastAPI()

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", ",".join(default_origins)).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(conversation_router, prefix="/api")
app.include_router(auth_router,prefix="/api")
app.include_router(file_router,prefix="/api")
app.include_router(settings_router,prefix="/api")
@app.get("/")
def read_root():
    return {
        "message":"Server is running"
    }
