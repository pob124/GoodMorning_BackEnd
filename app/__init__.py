# App package initialization 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.core.firebase import initialize_firebase

app = FastAPI(
    title="Good Morning API",
    version="25.05.02",
    description="Good Morning API 문서",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase 초기화
initialize_firebase()

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

__all__ = [
    # 서비스
    "initialize_firebase",
    # 모델
    "UserDB", "User", "UserProfile", "Token", "TokenData", "SignupData", "Base",
    # 설정
    "get_settings"
] 