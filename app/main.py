from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.config import get_settings
from app.api import router as api_router
from app.auth import router as auth_router
from app.services import initialize_firebase

# 코어 모듈 먼저 초기화
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 마이페이지 엔드포인트
app.include_router(api_router, prefix="", tags=["mypage"])

# 채팅방 엔드포인트
app.include_router(api_router, prefix="", tags=["chatrooms"])

# API 라우터 등록
app.include_router(api_router, prefix="/api", tags=["api"])

# 인증 라우터 등록
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"status": "API server is running", "app_name": settings.APP_NAME}

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})