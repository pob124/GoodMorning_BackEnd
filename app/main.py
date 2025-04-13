from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.core import get_settings
from app.api import router as api_router
from app.auth import router as auth_router

# 코어 모듈 먼저 초기화
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API 라우터 등록
app.include_router(api_router, prefix="/api")

# 인증 라우터 등록
app.include_router(auth_router, prefix="/auth")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})