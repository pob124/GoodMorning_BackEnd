# 🪟 Windows에서 Good Morning API 배포하기

## 📋 **준비사항**

### **1. 필수 소프트웨어 설치**
- **Docker Desktop for Windows**: https://www.docker.com/products/docker-desktop
- **Git**: https://git-scm.com/download/win

### **2. DuckDNS 설정**
1. https://www.duckdns.org 접속
2. GitHub/Google 계정으로 로그인
3. `goodmorningkr01` 도메인의 IP를 서버 IP로 설정

## 🚀 **배포 단계**

### **1단계: 프로젝트 준비**
```powershell
# PowerShell 관리자 권한으로 실행
cd C:\Project_GoodMorning\GoodMorning_BackEnd\docker
```

### **2단계: 환경변수 확인**
현재 `env.production` 파일이 다음과 같이 설정되어 있습니다:
- ✅ POSTGRES_PASSWORD: `your_secure_password_here`
- ✅ PGADMIN_PASSWORD: `your_admin_password_here`
- ✅ SSL_EMAIL: `hch3154@gmail.com`

### **3단계: 배포 실행**
```powershell
# PowerShell 스크립트 실행
.\deploy-production.ps1
```

만약 실행 정책 오류가 발생하면:
```powershell
# 실행 정책 변경 (일시적)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 다시 배포 실행
.\deploy-production.ps1
```

## 📊 **배포 과정**

배포 스크립트는 다음 단계를 자동으로 수행합니다:

1. **환경 확인** ✅
   - Docker 및 Docker Compose 설치 확인
   - 환경변수 파일 확인

2. **SSL 인증서 발급** 🔒
   - Let's Encrypt를 통한 무료 SSL 인증서 발급
   - `goodmorningkr01.duckdns.org` 도메인 인증

3. **서비스 시작** 🚀
   - PostgreSQL 데이터베이스
   - FastAPI 백엔드 서버
   - Nginx 리버스 프록시
   - PgAdmin 관리 도구

4. **헬스 체크** 🏥
   - API 서버 응답 확인
   - HTTPS 연결 테스트

## 🌐 **접속 정보**

배포 완료 후 다음 URL로 접속할 수 있습니다:

- **🌐 API 문서**: https://goodmorningkr01.duckdns.org/api/docs
- **🔧 PgAdmin**: https://goodmorningkr01.duckdns.org/pgadmin/
- **💬 WebSocket 테스트**: https://goodmorningkr01.duckdns.org/static/websocket_test.html

### **PgAdmin 로그인 정보**
- **이메일**: `hch3154@gmail.com`
- **비밀번호**: `your_admin_password_here`

## 🔧 **관리 명령어**

### **서비스 상태 확인**
```powershell
docker-compose -f docker-compose.prod.yml ps
```

### **로그 확인**
```powershell
# 전체 로그
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f db
```

### **서비스 재시작**
```powershell
docker-compose -f docker-compose.prod.yml restart
```

### **서비스 중지**
```powershell
docker-compose -f docker-compose.prod.yml down
```

### **서비스 시작**
```powershell
docker-compose -f docker-compose.prod.yml up -d
```

## 🔒 **SSL 인증서 갱신**

Let's Encrypt 인증서는 90일마다 갱신이 필요합니다:

```powershell
# 인증서 갱신
docker-compose -f docker-compose.prod.yml run --rm certbot renew

# Nginx 재시작
docker-compose -f docker-compose.prod.yml restart nginx
```

## 🆘 **문제 해결**

### **일반적인 문제들**

1. **Docker Desktop이 실행되지 않음**
   - Docker Desktop 앱을 시작하고 잠시 대기
   - WSL 2 백엔드가 활성화되어 있는지 확인

2. **포트 충돌**
   ```powershell
   # 포트 사용 중인 프로세스 확인
   netstat -ano | findstr :80
   netstat -ano | findstr :443
   ```

3. **방화벽 문제**
   - Windows Defender 방화벽에서 Docker 허용
   - 포트 80, 443 인바운드 규칙 추가

4. **DNS 전파 지연**
   - DuckDNS 설정 후 최대 24시간 대기
   - `nslookup goodmorningkr01.duckdns.org`로 확인

### **로그 확인**
```powershell
# 오류 발생 시 상세 로그 확인
docker-compose -f docker-compose.prod.yml logs --tail=100 web
```

## 📱 **프론트엔드 연결**

프론트엔드에서 API를 사용하려면:

```javascript
// API 기본 URL 설정
const API_BASE_URL = 'https://goodmorningkr01.duckdns.org/api';

// 환경변수로 관리 (권장)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://goodmorningkr01.duckdns.org/api';
```

## 🎉 **배포 완료!**

모든 단계가 완료되면 Good Morning API가 인터넷에서 접근 가능한 상태가 됩니다!

- 🌐 **API 문서**: https://goodmorningkr01.duckdns.org/api/docs
- 🔐 **HTTPS 보안 연결**
- 📊 **실시간 모니터링 가능**
- �� **자동 데이터베이스 백업** 