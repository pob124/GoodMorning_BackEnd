# 🐳 Good Morning API Docker 환경

## 📁 **폴더 구조**

```
docker/
├── 📋 README.md                    # 이 파일
├── 🐳 Dockerfile                   # Docker 이미지 빌드 설정
├── 🔧 docker-compose.yml           # 개발용 Docker Compose
├── 🚀 docker-compose.prod.yml      # 프로덕션용 Docker Compose
├── 🔑 firebase-adminsdk.json       # Firebase 인증 키
├── 🔑 firebase_token.json          # Firebase 토큰
│
├── 📚 docs/                        # 문서 모음
│   ├── DEPLOYMENT.md               # 일반 배포 가이드
│   ├── DUCKDNS_SETUP.md           # DuckDNS 설정 가이드
│   ├── WINDOWS_DEPLOY.md          # Windows 배포 가이드
│   └── PORT_FORWARDING_GUIDE.md   # 포트 포워딩 가이드
│
├── 🛠️ scripts/                     # 배포 스크립트
│   ├── deploy.sh                   # Linux/Mac 배포 스크립트
│   ├── deploy-production.sh        # Linux/Mac 프로덕션 배포
│   └── deploy-production.ps1       # Windows 프로덕션 배포
│
├── ⚙️ configs/                     # 설정 파일
│   ├── env.example                 # 환경변수 예시
│   ├── env.production              # 프로덕션 환경변수
│   └── heroku.yml                  # Heroku 배포 설정
│
├── 🗄️ backups/                     # 백업 파일
│   ├── default.conf.backup         # Nginx 설정 백업
│   └── ssl.conf.disabled           # 비활성화된 SSL 설정
│
└── 🌐 nginx/                       # Nginx 설정
    ├── conf.d/
    │   └── default.conf             # 현재 Nginx 설정
    ├── www/                         # 웹 루트 디렉토리
    └── ssl/                         # SSL 인증서 저장소
```

## 🚀 **빠른 시작**

### **개발 환경**
```bash
docker-compose up -d
```

### **프로덕션 환경 (Windows)**
```powershell
.\scripts\deploy-production.ps1
```

### **프로덕션 환경 (Linux/Mac)**
```bash
./scripts/deploy-production.sh
```

## 📖 **문서 가이드**

| 문서 | 설명 | 대상 |
|------|------|------|
| `docs/WINDOWS_DEPLOY.md` | Windows에서 배포하기 | Windows 사용자 |
| `docs/DUCKDNS_SETUP.md` | DuckDNS 도메인 설정 | 모든 사용자 |
| `docs/PORT_FORWARDING_GUIDE.md` | 포트 포워딩 설정 | 홈 서버 운영자 |
| `docs/DEPLOYMENT.md` | 클라우드 배포 가이드 | 클라우드 배포자 |

## ⚙️ **설정 파일**

### **환경변수 설정**
1. `configs/env.example`을 복사하여 `.env` 파일 생성
2. 필요한 값들을 수정

### **프로덕션 환경**
- `configs/env.production` 파일 사용
- 강력한 비밀번호로 설정됨

## 🔧 **주요 명령어**

### **서비스 관리**
```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 로그 확인
docker-compose logs -f

# 서비스 상태 확인
docker-compose ps
```

### **프로덕션 관리**
```bash
# 프로덕션 서비스 시작
docker-compose -f docker-compose.prod.yml up -d

# 프로덕션 로그 확인
docker-compose -f docker-compose.prod.yml logs -f
```

## 🌐 **접속 정보**

### **개발 환경**
- API 문서: http://localhost/api/docs
- PgAdmin: http://localhost/pgladmin/

### **프로덕션 환경**
- API 문서: https://goodmorningkr01.duckdns.org/api/docs
- PgAdmin: https://goodmorningkr01.duckdns.org/pgadmin/
- WebSocket 테스트: https://goodmorningkr01.duckdns.org/static/websocket_test.html

## 🔒 **보안 정보**

### **기본 계정 정보**
- **PgAdmin 이메일**: hch3154@gmail.com
- **PgAdmin 비밀번호**: configs/env.production 파일 참조

### **방화벽 설정**
- HTTP: 80번 포트
- HTTPS: 443번 포트

## 🆘 **문제 해결**

### **일반적인 문제**
1. **포트 충돌**: `docker-compose down` 후 재시작
2. **권한 오류**: 관리자 권한으로 실행
3. **네트워크 오류**: 방화벽 설정 확인

### **로그 확인**
```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs web
docker-compose logs nginx
docker-compose logs db
```

## 📊 **데이터베이스 스키마**

마이그레이션은 다음 테이블을 생성합니다:

1. `users` - 사용자 정보를 저장하는 테이블
2. `chatrooms` - 채팅방 정보를 저장하는 테이블
3. `messages` - 채팅 메시지를 저장하는 테이블

모든 테이블은 API 문서의 스키마에 맞게 설계되었습니다.

## 📞 **지원**

문제가 발생하면 다음 정보와 함께 문의:
- 오류 메시지
- 로그 내용
- 운영체제 정보
- Docker 버전
