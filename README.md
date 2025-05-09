# MHP_TEST 프로젝트

## 프로젝트 개요
MHP_TEST는 FastAPI 기반의 백엔드 서비스로, Firebase Authentication을 통한 사용자 인증과 API 서비스를 제공합니다.

## 프로젝트 구조
```
MHP_TEST/
├── app/                    # 메인 애플리케이션 코드
│   ├── api/               # API 엔드포인트
│   ├── core/              # 핵심 설정 및 유틸리티
│   ├── db/                # 데이터베이스 관련 코드
│   ├── docs/              # API 문서
│   ├── models/            # 데이터 모델
│   ├── schemas/           # Pydantic 스키마
│   ├── services/          # 비즈니스 로직
│   ├── utils/             # 유틸리티 함수
│   ├── main.py            # 앱 진입점
│   └── dependencies.py    # 의존성 주입
├── docker/                # Docker 관련 파일
│   ├── MHP_TEST/         # Docker 설정
│   ├── docker-compose.yml # Docker Compose 설정
│   ├── Dockerfile        # 도커 이미지 정의
│   └── firebase-adminsdk.json # Firebase 서비스 계정 키
├── alembic/              # 데이터베이스 마이그레이션
├── static/               # 정적 파일
├── templates/            # HTML 템플릿
├── requirements.txt      # Python 의존성
└── alembic.ini          # Alembic 설정
```

## 주요 기능
- Firebase Authentication 기반 사용자 인증
- JWT 토큰 기반 API 보안
- RESTful API 엔드포인트
- 데이터베이스 마이그레이션 (Alembic)
- Docker 컨테이너화

## 시작하기

### 필수 조건
- Python 3.8+
- Docker와 Docker Compose
- Firebase 프로젝트

### 설치 및 실행

1. 저장소 클론
```bash
git clone [repository-url]
cd MHP_TEST
```

2. Docker 환경에서 실행
```bash
cd docker
docker-compose up --build
```

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export GOOGLE_APPLICATION_CREDENTIALS=docker/firebase-adminsdk.json

# 앱 실행
uvicorn app.main:app --reload
```

## API 문서
- Swagger UI: http://localhost:9090/docs
- ReDoc: http://localhost:9090/redoc

### Swagger UI 인증 방법
1. Swagger UI 페이지(http://localhost:9090/docs)에 접속합니다.
2. 우측 상단의 "Authorize" 버튼을 클릭합니다.
3. 팝업 창에서 다음과 같이 입력:
   - Value: `Bearer [your_jwt_token]`
   - 예시: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
4. "Authorize" 버튼을 클릭하여 인증을 완료합니다.
5. 이제 보호된 API 엔드포인트에 접근할 수 있습니다.

> 참고: JWT 토큰은 로그인 API를 통해 얻을 수 있습니다.
> 
> 1. Firebase Authentication을 통해 ID 토큰을 얻습니다.
> 2. 다음 curl 명령어로 서버에 인증 요청을 보냅니다:
> ```powershell
> # 1. 커스텀 토큰 받기 (예시)
> $body = @{ token = "YOUR_FIREBASE_UID" } | ConvertTo-Json
> $response = Invoke-RestMethod -Method Post -Uri "http://localhost:9090/api/auth/login" -Headers @{"Content-Type" = "application/json"} -Body $body
> $customToken = $response.access_token
> 
> # 2. 커스텀 토큰을 ID 토큰으로 교환
> $firebaseBody = @{
>     token = $customToken
>     returnSecureToken = $true
> } | ConvertTo-Json
> 
> try {
>     $firebaseResponse = Invoke-RestMethod `
>         -Method Post `
>         -Uri "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=YOUR_FIREBASE_WEB_API_KEY" ` 
>         -Headers @{"Content-Type" = "application/json"} `
>         -Body $firebaseBody `
>         -ErrorAction Stop
> 
>     Write-Host "`n[Firebase 응답]" ($firebaseResponse | ConvertTo-Json)
>     $idToken = $firebaseResponse.idToken
>     Write-Host "`n[ID 토큰] $idToken"
> } catch {
>     Write-Host "`n[에러 발생] $($_.Exception.Message)"
>     if ($_.Exception.Response -ne $null) {
>         $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
>         $reader.BaseStream.Position = 0
>         $reader.DiscardBufferedData()
>         $responseBody = $reader.ReadToEnd()
>         Write-Host "`n[응답 내용] $responseBody"
>     }
> }
> ```
> 
> > 참고: 
> > - `YOUR_FIREBASE_UID`: Firebase Authentication에서 발급받은 사용자 UID
> > - `YOUR_FIREBASE_WEB_API_KEY`: Firebase 콘솔의 프로젝트 설정에서 확인할 수 있는 웹 API 키
> 
> 응답으로 받은 JWT 토큰을 Swagger UI의 Authorize에 입력하면 됩니다.

## 데이터베이스 마이그레이션
```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "migration message"

# 마이그레이션 적용
alembic upgrade head
```
## 환경 변수
- `GOOGLE_APPLICATION_CREDENTIALS`: Firebase 서비스 계정 키 파일 경로
- `DATABASE_URL`: 데이터베이스 연결 URL
- `SECRET_KEY`: JWT 토큰 암호화 키

## 라이선스
이 프로젝트는 MIT 라이선스 하에 배포됩니다.
