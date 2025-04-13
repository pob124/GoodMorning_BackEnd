# FastAPI Firebase Authentication 프로젝트

FastAPI와 Firebase Authentication을 사용한 인증 시스템 구현 프로젝트입니다.

## 주요 기능

- Firebase 기반 이메일/비밀번호 인증
- Google 소셜 로그인
- 보호된 API 엔드포인트
- JWT 토큰 기반 인증
- Docker 컨테이너화

## 프로젝트 구조

```
project/
├── app/                    # 메인 애플리케이션 코드
│   ├── api/                # API 엔드포인트
│   ├── auth/               # 인증 관련 코드
│   ├── core/               # 핵심 설정 및 유틸리티
│   │   ├── config.py      # 앱 설정
│   │   ├── firebase.py    # Firebase 초기화
│   ├── models/             # 데이터 모델
│   ├── tests/              # 테스트 코드
│   └── main.py             # 앱 진입점
├── docker/                 # Docker 관련 파일
│   ├── Dockerfile          # 도커 이미지 정의
│   ├── docker-compose.yml  # Docker Compose 설정
│   └── firebase-adminsdk.json  # Firebase 서비스 계정 키
├── static/                 # 정적 파일 (CSS, JS)
│   └── css/
│       └── styles.css      # 스타일시트
├── templates/              # HTML 템플릿
│   └── index.html          # 로그인 테스트 페이지
├── requirements.txt        # Python 의존성
└── README.md               # 이 파일
```

## 시작하기

### 필수 조건

- Python 3.8+
- Docker와 Docker Compose
- Firebase 프로젝트

### Firebase 설정

1. [Firebase 콘솔](https://console.firebase.google.com)에서 새 프로젝트 생성
2. Authentication 서비스 활성화
   - 이메일/비밀번호 로그인 방식 활성화
   - 구글 로그인 방식 활성화
3. 웹 애플리케이션 등록
   - 제공된 Firebase 설정(apiKey, projectId 등)을 `templates/index.html` 파일의 `firebaseConfig` 객체에 복사
4. 서비스 계정 키 발급
   - 프로젝트 설정 > 서비스 계정 > Firebase Admin SDK > 새 비공개 키 생성
   - 다운로드된 JSON 파일을 `docker/firebase-adminsdk.json`로 저장

### 설치 및 실행

#### Docker 환경에서 실행 (권장)

1. 저장소 클론
   ```bash
   git clone [repository-url]
   cd [project-directory]
   ```

2. Firebase 설정 준비
   - Firebase 서비스 계정 키를 `docker/firebase-adminsdk.json`에 저장
   - `templates/index.html` 파일의 `firebaseConfig` 객체를 실제 Firebase 프로젝트 설정으로 업데이트

3. Docker Compose로 빌드 및 실행
   ```bash
   cd docker
   docker-compose build web
   docker-compose up web
   ```

4. 브라우저에서 접속
   - http://localhost:8000

5. 로그 확인 (문제 해결)
   ```bash
   # 실시간 로그 확인
   docker-compose logs -f web
   ```

6. 컨테이너 종료
   ```bash
   # Ctrl+C로 종료 또는 다른 터미널에서
   docker-compose down
   ```

#### 로컬 개발 환경

1. 가상환경 생성 및 활성화
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

3. 환경 변수 설정
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=docker/firebase-adminsdk.json
   ```

4. 앱 실행
   ```bash
   uvicorn app.main:app --reload
   ```

## 테스트

### Docker로 테스트 실행
```bash
cd docker
docker-compose build test
docker-compose up test
```

### 로컬에서 테스트 실행
```bash
pytest -v app/tests
```

## 구글 로그인 테스트

### Docker 환경에서 구글 로그인 테스트

1. Firebase 콘솔에서 필수 설정 확인
   - Authentication > Sign-in method > Google 로그인이 활성화되어 있는지 확인
   - Authentication > Settings > Authorized domains에 "localhost"가 추가되어 있는지 확인

2. Docker 컨테이너 실행
   ```bash
   cd docker
   docker-compose up web
   ```

3. 브라우저에서 테스트
   - http://localhost:8000 접속
   - "Google로 로그인" 버튼 클릭
   - 구글 계정으로 로그인
   - 로그인 성공 시 사용자 정보 표시
   - "보호된 API 호출" 버튼으로 인증된 API 요청 테스트

4. 문제 해결
   - Firebase 초기화 문제: Docker 로그 확인 (`docker-compose logs -f web`)
   - 브라우저 콘솔(F12) 확인으로 클라이언트 측 오류 디버깅
   - API 키 오류: `templates/index.html`의 Firebase 설정 값 확인

### 로컬 환경에서 구글 로그인 테스트

애플리케이션이 실행된 상태에서 동일한 단계로 테스트할 수 있습니다:
1. http://localhost:8000 접속
2. "Google로 로그인" 버튼 클릭
3. 구글 계정 선택 및 인증
4. 로그인 성공 시 사용자 정보 확인
5. "보호된 API 호출" 버튼으로 인증 테스트

## API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 보안 주의사항

- Firebase 서비스 계정 키(`firebase-adminsdk.json`)는 절대 공개 저장소에 커밋하지 마세요
- 테스트 목적이라도 가능한 Firebase Admin SDK 키는 환경 변수로 관리하세요
- 프로덕션 환경에서는 CORS 설정을 적절히 제한하세요

## 라이선스

MIT 

## MHP_TEST 사용 가능한 기능 및 절차

### 사용 가능한 기능

#### 1. 사용자 인증 및 관리
- 이메일/비밀번호 회원가입 및 로그인
- 구글 소셜 로그인
- 사용자 프로필 관리
- 비밀번호 재설정

#### 2. 데이터베이스 연동
- PostgreSQL 데이터베이스 연동
- Alembic을 통한 데이터베이스 마이그레이션 관리
- 사용자 데이터 CRUD 작업

#### 3. API 기능
- JWT 토큰 기반 인증된 API 엔드포인트
- Swagger 및 ReDoc을 통한 API 문서화
- API 버전 관리

#### 4. 배포 및 인프라
- Docker 컨테이너화
- Docker Compose를 통한 다중 서비스 관리
- Firebase Admin SDK 통합

### 사용 절차

#### 개발 환경 설정
1. 소스 코드 클론
   ```bash
   git clone [repository-url]
   cd MHP_TEST
   ```

2. 가상환경 설정
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. 패키지 설치
   ```bash
   pip install -r requirements.txt
   ```

4. Firebase 서비스 계정 키 설정
   - `docker/firebase-adminsdk.json` 파일 확인 또는 생성

#### 데이터베이스 마이그레이션
1. 마이그레이션 실행
   ```bash
   alembic upgrade head
   ```

2. 새 마이그레이션 생성 (스키마 변경 시)
   ```bash
   alembic revision --autogenerate -m "설명"
   ```

#### 로컬 서버 실행
1. FastAPI 서버 실행
   ```bash
   uvicorn app.main:app --reload
   ```

2. 서버 접속
   - API 서버: http://localhost:8000
   - API 문서: http://localhost:8000/docs

#### Docker 환경에서 실행
1. Docker 컨테이너 빌드 및 실행
   ```bash
   cd docker
   docker-compose up -d
   ```

2. 컨테이너 로그 확인
   ```bash
   docker-compose logs -f
   ```

#### 테스트 실행
1. 전체 테스트 실행
   ```bash
   pytest
   ```

2. 특정 테스트 파일 실행
   ```bash
   pytest app/tests/test_auth.py -v
   ```

### 문제 해결

- **Firebase 연결 오류**: Firebase 서비스 계정 키 파일이 올바른 위치에 있는지 확인하세요.
- **데이터베이스 연결 오류**: PostgreSQL 연결 문자열과 데이터베이스 서버 실행 여부를 확인하세요.
- **API 응답 오류**: 로그를 확인하고 JWT 토큰이 유효한지 확인하세요. 