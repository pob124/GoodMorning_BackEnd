## 기술 스택
- **백엔드**: FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **인증**: Firebase Authentication
- **통신**: WebSockets
- **배포**: Docker, Nginx

## 시작하기

### 필수 요구사항
- Python 3.8 이상
- PostgreSQL
- Firebase 계정 및 프로젝트

### 설치 및 설정

1. 저장소 복제:
```bash
git https://github.com/pob124/GoodMorning_BackEnd
cd GoodMorning_BackEnd
```

**Docker 환경에서 실행:**
Docker를 사용한 전체 환경 설정 및 실행 방법은 [docker/README.md](docker/README.md)를 참조하세요.

## API 문서
API 문서는 서버 실행 후 `/docs` 경로에서 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주요 기능
- 사용자 프로필 관리
- 채팅방 생성 및 관리
- 실시간 메시지 교환 (WebSocket)
- 위치 기반 파트너 검색

## 채팅 시스템 아키텍처

### 📱 클라이언트 API 엔드포인트
```
📱 클라이언트
├── 메시지 전송: POST /api/chat/{room_id} (HTTP)
├── 메시지 조회: GET /api/chat/{room_id} (HTTP)  
├── 검색: GET /api/chat/search (HTTP)
└── 실시간 알림: ws://localhost/api/ws/chat/{room_id} (WebSocket)
```

### 🔄 메시지 플로우
```
1. 클라이언트 A가 POST /api/chat/{room_id}로 메시지 전송
2. 서버가 DB에 저장 후 WebSocket으로 모든 연결된 사용자에게 브로드캐스트
3. 클라이언트 B, C가 WebSocket으로 실시간 메시지 수신
```

### 🏗️ 아키텍처 설계 원칙

#### REST API (chat.py) - 핵심 채팅 기능
- **메시지 전송**: `POST /api/chat/{room_id}`
- **메시지 조회**: `GET /api/chat/{room_id}`
- **메시지 검색**: `GET /api/chat/search`
- **활성 사용자**: `GET /api/chat/{room_id}/active-users`
- **메시지 읽음 처리**: `PATCH /api/chat/{room_id}/messages/{message_id}/read`

**장점:**
- 안정적인 HTTP 요청/응답
- 명확한 오류 처리
- 오프라인 상태에서도 사용 가능
- 표준 REST API 패턴

#### WebSocket (websocket.py) - 실시간 보조 기능
- **실시간 알림 수신**: 새 메시지, 사용자 입장/퇴장
- **연결 상태 관리**: Ping/Pong, 활성 사용자 추적
- **시스템 메시지**: 접속 알림, 상태 변경

**지원 메시지 타입:**
- `auth`: 인증 (필수 - 첫 번째 메시지)
- `ping`: 연결 상태 확인
- `get_active_users`: 활성 사용자 목록 요청

**응답 메시지 타입:**
- `message_response`: 새로운 채팅 메시지 (REST API로 전송된 메시지의 실시간 알림)
- `system`: 시스템 메시지 (입장/퇴장 알림)
- `user_status`: 사용자 상태 변경
- `error`: 오류 메시지
- `success`: 성공 메시지
- `pong`: ping에 대한 응답
- `active_users_response`: 활성 사용자 목록

### 🔐 인증 방식

#### REST API
- **방식**: JWT 토큰을 Authorization 헤더에 포함
- **형식**: `Authorization: Bearer {firebase_id_token}`

#### WebSocket
- **방식**: 연결 후 첫 번째 메시지로 인증
- **형식**: `{"type": "auth", "token": "firebase_id_token"}`

### 🧪 테스트 방법

#### WebSocket 테스트
1. 브라우저에서 `http://localhost/static/websocket_test.html` 접속
2. 채팅방 ID와 Firebase ID 토큰 입력
3. WebSocket 연결 및 실시간 기능 테스트

#### REST API 테스트
- Swagger UI: `http://localhost/docs`
- 각 엔드포인트별 상세 문서 및 테스트 인터페이스 제공

# Firebase UID를 파라미터로 받음 (기본값 제공)
param(
    [string]$uid = "XeLN0xL76oZPl6x8mnFEABQY54i1"
)

# Firebase API 키 (여기에 실제 키 입력)
$FIREBASE_API_KEY = "YOUR_FIREBASE_API_KEY"

# 백엔드 서버 URL
$API_BASE_URL = "http://localhost"

Write-Host "1. Firebase UID: $uid" -ForegroundColor Cyan

# 1단계: /api/auth/login에서 커스텀 토큰 얻기
try {
    Write-Host "2. 커스텀 토큰 요청 중..." -ForegroundColor Cyan
    $loginResponse = Invoke-RestMethod -Uri "$API_BASE_URL/api/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body (@{
            "token" = $uid
        } | ConvertTo-Json)

    $customToken = $loginResponse.access_token
    Write-Host "3. 커스텀 토큰 발급 성공!" -ForegroundColor Green
    Write-Host "   $($customToken.Substring(0, 30))..." -ForegroundColor Gray
}
catch {
    Write-Host "커스텀 토큰 발급 실패: $_" -ForegroundColor Red
    exit 1
}

# 2단계: 커스텀 토큰을 ID 토큰으로 교환
try {
    Write-Host "4. 커스텀 토큰을 ID 토큰으로 교환 중..." -ForegroundColor Cyan
    $tokenResponse = Invoke-RestMethod -Uri "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=$FIREBASE_API_KEY" `
        -Method POST `
        -ContentType "application/json" `
        -Body (@{
            "token" = $customToken;
            "returnSecureToken" = $true
        } | ConvertTo-Json)

    $idToken = $tokenResponse.idToken
    Write-Host "5. ID 토큰 교환 성공!" -ForegroundColor Green
    Write-Host "   $($idToken.Substring(0, 30))..." -ForegroundColor Gray
    
    # 클립보드에 ID 토큰 복사
    $idToken | Set-Clipboard
    Write-Host "6. ID 토큰이 클립보드에 복사되었습니다!" -ForegroundColor Green
    
    # 토큰 정보 파일로 저장
    $tokenInfo = @{
        "uid" = $uid
        "customToken" = $customToken
        "idToken" = $idToken
        "timestamp" = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    
    $tokenInfo | ConvertTo-Json | Out-File -FilePath "firebase_token.json" -Encoding utf8
    Write-Host "7. 토큰 정보가 firebase_token.json 파일에 저장되었습니다." -ForegroundColor Green
    
    # 상세한 ID 토큰 정보 출력
    Write-Host "`n============ ID 토큰 정보 ============" -ForegroundColor Yellow
    Write-Host "ID 토큰: $idToken"
    Write-Host "만료 시간: $($tokenResponse.expiresIn) 초"
    Write-Host "=======================================" -ForegroundColor Yellow
    
    Write-Host "`n✓ ID 토큰을 SwaggerUI Authorize 버튼에 붙여넣어 인증하세요!" -ForegroundColor Magenta
}
catch {
    Write-Host "ID 토큰 교환 실패: $_" -ForegroundColor Red
    exit 1
}