from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer
from app.core.firebase import initialize_firebase
from app.api import router as api_router
from app.utils.init_data import init_application_data
import logging
import time
import os
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
from fastapi.openapi.utils import get_openapi
import json

# 로깅 설정 - UTF-8 인코딩 강화
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

# 애플리케이션 초기화 - UTF-8 응답 처리 추가
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
    * **한국어 지원**: UTF-8 인코딩으로 한국어 완벽 지원
    
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

# 커스텀 JSON Response 클래스 - 한국어 처리 강화
class UnicodeJSONResponse(JSONResponse):
    def __init__(self, content, **kwargs):
        super().__init__(content, **kwargs)
        
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,  # 한국어 유니코드 문자 그대로 출력
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# 미들웨어: 요청 로깅 및 UTF-8 응답 처리
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # UTF-8 Content-Type 헤더 추가
            if "application/json" in response.headers.get("content-type", ""):
                response.headers["content-type"] = "application/json; charset=utf-8"
            
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
            return UnicodeJSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

# 미들웨어 등록
app.add_middleware(LoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS 설정 - 한국어 헤더 처리 포함
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용하는 것이 좋음
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "charset"]  # charset 헤더 노출
)

# 정적 파일 디렉토리 확인 및 생성
static_dir = "static"
if not os.path.exists(static_dir):
    try:
        os.makedirs(static_dir)
        logger.info(f"정적 파일 디렉토리 '{static_dir}'를 생성했습니다.")
        
        # 기본 index.html 파일 생성
        with open(os.path.join(static_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html>\n<html>\n<head>\n<meta charset='UTF-8'>\n<title>MHP Static Files</title>\n</head>\n<body>\n<h1>정적 파일 서비스</h1>\n<p>한국어 테스트: 안녕하세요! 🌅</p>\n</body>\n</html>")
        
    except Exception as e:
        logger.warning(f"정적 파일 디렉토리 생성 실패: {str(e)}")

# 정적 파일 제공
try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info("정적 파일 제공 경로가 설정되었습니다: /static")
except Exception as e:
    logger.warning(f"정적 파일 서비스 설정 실패: {str(e)}")

# 전역 예외 처리 - 한국어 메시지 지원
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"전역 예외 발생: {str(exc)}")
    return UnicodeJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "서버 내부 오류가 발생했습니다", "error": str(exc)}
    )

# 애플리케이션 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트"""
    logger.info("🌅 Project GoodMorning API 시작됨")
    logger.info("한국어 지원이 활성화되었습니다")
    
    # Firebase 초기화
    initialize_firebase()
    logger.info("Firebase 초기화 완료")
    
    # 기본 데이터 초기화 (기본 채팅방 생성)
    try:
        await init_application_data()
        logger.info("기본 데이터 초기화 완료")
    except Exception as e:
        logger.error(f"기본 데이터 초기화 실패: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트"""
    logger.info("🌙 Project GoodMorning API 종료됨")

# API 라우터 등록
app.include_router(api_router, prefix="/api")

# 루트 경로
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <meta charset="UTF-8">
            <title>Project GoodMorning API</title>
        </head>
        <body>
            <h1>🌅 Project GoodMorning API</h1>
            <p>한국어 지원이 가능한 아침 활동 플랫폼 API입니다.</p>
            <ul>
                <li><a href="/api/docs">📚 API 문서 (Swagger UI)</a></li>
                <li><a href="/api/redoc">📖 API 문서 (ReDoc)</a></li>
                <li><a href="/static">📁 정적 파일</a></li>
            </ul>
            <p>테스트: 안녕하세요! 🌄</p>
        </body>
    </html>
    """

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return UnicodeJSONResponse(
        content={
            "status": "healthy",
            "message": "서비스가 정상 작동 중입니다",
            "korean_test": "한국어 테스트 성공! 🎉",
            "version": "1.0.0"
        }
    )

# 한국어 테스트 엔드포인트
@app.get("/api/test/korean")
async def korean_test():
    return UnicodeJSONResponse(
        content={
            "message": "한국어 인코딩 테스트",
            "test_data": {
                "name": "김철수",
                "bio": "안녕하세요! 아침 등산을 좋아합니다. 🌄",
                "location": "서울, 대한민국",
                "emoji": "🌅🏃‍♂️☕🧘‍♂️📚"
            },
            "status": "성공"
        }
    )

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