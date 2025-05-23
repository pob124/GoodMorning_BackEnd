# Morning Hiking Partner 데이터베이스 설정

이 프로젝트는 데이터베이스 설정을 위해 Alembic 마이그레이션 시스템을 사용합니다.

## 데이터베이스 설정 방법

### 사전 요구사항

- PostgreSQL이 설치되어 있어야 합니다.
- Python과 필요한 패키지가 설치되어 있어야 합니다.

### 데이터베이스 마이그레이션 실행

프로젝트 루트 디렉토리에서 다음 명령을 실행합니다:

```bash
# 모든 마이그레이션을 적용
alembic upgrade head
```

이 명령은 통합 마이그레이션 파일(`alembic/versions/unified_migration.py`)을 사용하여 필요한 모든 테이블을 생성합니다.

### 데이터베이스 연결 설정

데이터베이스 연결 정보는 `alembic.ini` 파일에서 설정할 수 있습니다:

```
sqlalchemy.url = postgresql://사용자명:비밀번호@호스트:포트/데이터베이스명
```

예시:
```
sqlalchemy.url = postgresql://postgres:password@localhost:5432/mhp_db
```

## 스키마 구조

마이그레이션은 다음 테이블을 생성합니다:

1. `users` - 사용자 정보를 저장하는 테이블
2. `chatrooms` - 채팅방 정보를 저장하는 테이블
3. `messages` - 채팅 메시지를 저장하는 테이블

모든 테이블은 API 문서의 스키마에 맞게 설계되었습니다. 