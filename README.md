

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
git clone https://github.com/yourusername/morning-hiking-partner.git
cd morning-hiking-partner
```

2. 가상 환경 설정:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
`.env` 파일을 생성하고 필요한 환경 변수를 설정합니다:
```
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=mhp_db
DB_HOST=localhost
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
```

5. 데이터베이스 마이그레이션:
```bash
alembic upgrade head
```

### 실행 방법

개발 서버 실행:
```bash
uvicorn app.main:app --reload
```

## API 문서
API 문서는 서버 실행 후 `/docs` 경로에서 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주요 기능
- 사용자 프로필 관리
- 채팅방 생성 및 관리
- 실시간 메시지 교환 (WebSocket)
- 위치 기반 파트너 검색


# Firebase UID를 파라미터로 받음 (기본값 제공)
param(
    [string]$uid = "XeLN0xL76oZPl6x8mnFEABQY54i1"
)

# Firebase API 키 (여기에 실제 키 입력)
$FIREBASE_API_KEY = "AIzaSyDRaQSVa4st5HGk9w9-v02wt4XvI9PP38k"

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