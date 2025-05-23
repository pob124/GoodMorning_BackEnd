# Morning Hiking Partner (MHP)

## 프로젝트 소개
Morning Hiking Partner는 함께 등산할 파트너를 찾을 수 있는 애플리케이션입니다. 위치 기반으로 근처에 있는 등산 파트너를 찾아 채팅을 통해 연결해줍니다.

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
