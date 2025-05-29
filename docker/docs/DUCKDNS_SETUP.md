# 🦆 DuckDNS 도메인 배포 가이드

## 📍 도메인 정보
- **도메인**: `goodmorningkr01.duckdns.org`
- **서비스**: Good Morning API

## 🚀 **배포 단계**

### **1단계: DuckDNS 설정 확인**

1. **DuckDNS 계정 로그인**
   - https://www.duckdns.org 접속
   - GitHub/Google 계정으로 로그인

2. **도메인 IP 업데이트**
   ```bash
   # 현재 서버의 공인 IP 확인
   curl ifconfig.me
   
   # DuckDNS에서 goodmorningkr01 도메인의 IP를 위 IP로 설정
   ```

3. **자동 IP 업데이트 설정 (선택사항)**
   ```bash
   # crontab에 추가하여 IP 자동 업데이트
   */5 * * * * curl "https://www.duckdns.org/update?domains=goodmorningkr01&token=YOUR_TOKEN&ip="
   ```

### **2단계: 서버 환경 준비**

1. **필수 소프트웨어 설치**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install docker.io docker-compose git curl -y
   sudo usermod -aG docker $USER
   
   # 재로그인 또는 newgrp docker
   ```

2. **방화벽 설정**
   ```bash
   # UFW 방화벽 설정
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw status
   ```

### **3단계: 프로젝트 배포**

1. **프로젝트 클론**
   ```bash
   git clone https://github.com/your-repo/GoodMorning_BackEnd.git
   cd GoodMorning_BackEnd/docker
   ```

2. **환경변수 설정**
   ```bash
   # env.production 파일 수정
   nano env.production
   
   # 다음 값들을 반드시 변경하세요:
   # POSTGRES_PASSWORD=your_strong_password_here
   # PGADMIN_PASSWORD=your_admin_password_here
   # SSL_EMAIL=your-email@example.com
   ```

3. **배포 실행**
   ```bash
   # 실행 권한 부여
   chmod +x deploy-production.sh
   
   # 배포 실행
   ./deploy-production.sh
   ```

### **4단계: 배포 확인**

배포가 완료되면 다음 URL들에 접근할 수 있습니다:

- **🌐 API 문서**: https://goodmorningkr01.duckdns.org/api/docs
- **🔧 PgAdmin**: https://goodmorningkr01.duckdns.org/pgadmin/
- **💬 WebSocket 테스트**: https://goodmorningkr01.duckdns.org/static/websocket_test.html

## 🔧 **관리 명령어**

### **서비스 관리**
```bash
# 서비스 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f web

# 서비스 재시작
docker-compose -f docker-compose.prod.yml restart

# 서비스 중지
docker-compose -f docker-compose.prod.yml down

# 서비스 시작
docker-compose -f docker-compose.prod.yml up -d
```

### **SSL 인증서 갱신**
```bash
# 인증서 갱신 (90일마다 필요)
docker-compose -f docker-compose.prod.yml run --rm certbot renew
docker-compose -f docker-compose.prod.yml restart nginx
```

### **데이터베이스 백업**
```bash
# 데이터베이스 백업
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres mhp_db > backup_$(date +%Y%m%d).sql

# 백업 복원
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres mhp_db < backup_20240101.sql
```

## 🔒 **보안 설정**

### **환경변수 보안**
- `POSTGRES_PASSWORD`: 강력한 비밀번호 사용 (예: random_string_123!)
- `PGADMIN_PASSWORD`: PgAdmin 접근용 비밀번호 (예: admin_password_456!)
- `SSL_EMAIL`: Let's Encrypt 알림용 이메일

### **방화벽 설정**
```bash
# 필요한 포트만 열기
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 5432/tcp  # PostgreSQL (외부 접근 차단)
```

### **정기 업데이트**
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 이미지 업데이트
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 **모니터링**

### **시스템 리소스 확인**
```bash
# 디스크 사용량
df -h

# 메모리 사용량
free -h

# Docker 컨테이너 리소스 사용량
docker stats
```

### **로그 모니터링**
```bash
# 실시간 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f db
```

## 🆘 **문제 해결**

### **일반적인 문제들**

1. **도메인 접근 불가**
   - DuckDNS IP 설정 확인
   - 방화벽 설정 확인
   - DNS 전파 대기 (최대 24시간)

2. **SSL 인증서 오류**
   ```bash
   # 인증서 재발급
   docker-compose -f docker-compose.prod.yml run --rm certbot certonly --webroot --webroot-path=/var/www/html --email your-email@example.com --agree-tos --no-eff-email --force-renewal -d goodmorningkr01.duckdns.org
   ```

3. **데이터베이스 연결 오류**
   - 환경변수 확인
   - 컨테이너 재시작
   ```bash
   docker-compose -f docker-compose.prod.yml restart db web
   ```

4. **메모리 부족**
   ```bash
   # 사용하지 않는 Docker 이미지 정리
   docker system prune -a
   ```

## 📞 **지원**

문제가 발생하면 다음 정보와 함께 문의하세요:
- 오류 메시지
- 로그 내용: `docker-compose -f docker-compose.prod.yml logs`
- 시스템 정보: `uname -a`, `docker --version` 