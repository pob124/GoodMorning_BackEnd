from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer
from app.core.firebase import initialize_firebase
from app.api import router as api_router
import logging
import time
import os
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
from fastapi.openapi.utils import get_openapi

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("mhp-api")

# 보안 스키마 정의
security = HTTPBearer()

# 애플리케이션 초기화
app = FastAPI(
    title="Project GoodMorning API",
    description="""
    Project GoodMorning Application API v1.0.0
    
    ## 🔐 Authentication
    
    이 API는 **Firebase Authentication**을 사용합니다.
    
    ### 인증 방법:
    1. Firebase 클라이언트에서 로그인하여 **ID Token** 획득
    2. 요청 헤더에 `Authorization: Bearer <firebase_id_token>` 추가
    3. 아래 **Authorize** 버튼을 클릭하여 토큰 입력
    
    ### 테스트용 토큰 획득:
    - `/api/auth/login` 엔드포인트에 Firebase UID를 전송하여 Custom Token 획득 가능
    - 실제 운영에서는 Firebase 클라이언트 SDK 사용 권장
    
    ## Features
    
    * **REST API**: 표준 HTTP 엔드포인트
    * **WebSocket**: 실시간 채팅 및 알림
    * **Firebase Auth**: 인증 및 권한 관리
    * **PostgreSQL**: 데이터 저장소
    
    ## WebSocket Support
    
    이 API는 실시간 채팅을 위한 WebSocket 엔드포인트를 제공합니다:
    
    **엔드포인트**: `ws://localhost/api/ws/chat/{room_id}`
    
    **참고**: WebSocket 엔드포인트는 Swagger UI에서 완전히 테스트할 수 없습니다. 
    WebSocket 클라이언트 도구나 JavaScript를 사용하여 테스트하세요.
    
    ## API Documentation
    
    * **Swagger UI**: `/api/docs` (이 페이지)
    * **ReDoc**: `/api/redoc`
    * **OpenAPI JSON**: `/api/openapi.json`
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 미들웨어: 요청 로깅
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} "
                f"완료: {response.status_code} ({process_time:.3f}s)"
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"{request.method} {request.url.path} "
                f"오류: {str(e)} ({process_time:.3f}s)"
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

# 미들웨어 등록
app.add_middleware(LoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용하는 것이 좋음
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 디렉토리 확인 및 생성
static_dir = "static"
if not os.path.exists(static_dir):
    try:
        os.makedirs(static_dir)
        logger.info(f"정적 파일 디렉토리 '{static_dir}'를 생성했습니다.")
        
        # 기본 index.html 파일 생성
        with open(os.path.join(static_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html>\n<html>\n<head>\n<title>MHP Static Files</title>\n</head>\n<body>\n<h1>정적 파일 서비스</h1>\n</body>\n</html>")
        
    except Exception as e:
        logger.warning(f"정적 파일 디렉토리 생성 실패: {str(e)}")

# 정적 파일 제공
try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info("정적 파일 제공 경로가 설정되었습니다: /static")
except Exception as e:
    logger.warning(f"정적 파일 서비스 설정 실패: {str(e)}")

# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"전역 예외 발생: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# 시작 이벤트
@app.on_event("startup")
async def startup_event():
    logger.info("애플리케이션 시작...")
    initialize_firebase()
    logger.info("Firebase 초기화 완료")

# 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("애플리케이션 종료...")

# API 라우터 등록
app.include_router(api_router, prefix="/api")

# 루트 경로
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Project GoodMorning API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 10px;
                }
                .links {
                    margin-top: 20px;
                }
                .links a {
                    display: inline-block;
                    margin-right: 20px;
                    color: #3498db;
                    text-decoration: none;
                }
                .links a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <h1>Project Good Morning</h1>
            <p>Welcome to GoodMorning Partner API. This API provides endpoints for managing goodMorning partners and chat rooms.</p>
            
            <div class="links">
                <a href="/api/docs">Swagger UI Documentation</a>
                <a href="/api/redoc">ReDoc Documentation</a>
                <a href="/static/websocket_test.html">WebSocket 테스트</a>
                <a href="/pgadmin/">PgAdmin</a>
            </div>
        </body>
    </html>
    """

# 커스텀 OpenAPI 스키마 생성
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # OAuth2 보안 스키마 추가
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/auth/token",
                    "scopes": {}
                }
            },
            "description": "Username: 아무 값, Password: Firebase ID Token을 입력하세요"
        }
    }
    
    # 전역 보안 설정 (선택적)
    # openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 직접 실행 시 서버 구동
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)