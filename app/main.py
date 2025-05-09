from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.firebase import initialize_firebase
from app.api import router as api_router

app = FastAPI(
    title="MHP API",
    description="MHP(Morning Hiking Partner) API",
    version="1.0.0"
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
@app.on_event("startup")
async def startup_event():
    initialize_firebase()

# API 라우터 등록
app.include_router(api_router, prefix="/api")