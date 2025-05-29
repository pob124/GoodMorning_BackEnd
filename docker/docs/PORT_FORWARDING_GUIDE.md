# 🌐 포트 포워딩 설정 가이드

## 📍 **현재 상황**
- **도메인**: `goodmorningkr01.duckdns.org`
- **현재 IP**: `175.112.153.69`
- **문제**: 외부에서 접속 시 공유기 설정 페이지가 나타남
- **원인**: 포트 포워딩 미설정

## 🔧 **해결 방법**

### **1단계: 공유기 관리 페이지 접속**

1. **공유기 IP 확인**
   ```powershell
   # Windows에서 게이트웨이 IP 확인
   ipconfig
   # 기본 게이트웨이 주소를 확인 (보통 192.168.1.1 또는 192.168.0.1)
   ```

2. **공유기 관리 페이지 접속**
   - 브라우저에서 `http://192.168.1.1` 또는 `http://192.168.0.1` 접속
   - 관리자 계정으로 로그인

### **2단계: 포트 포워딩 설정**

**설정해야 할 포트들:**
- **HTTP**: 80번 포트
- **HTTPS**: 443번 포트

**설정 방법:**
1. **포트 포워딩/가상 서버** 메뉴 찾기
2. **새 규칙 추가**:
   ```
   서비스 이름: Good Morning API HTTP
   외부 포트: 80
   내부 포트: 80
   내부 IP: [현재 컴퓨터 IP]
   프로토콜: TCP
   ```
   
3. **HTTPS 규칙 추가**:
   ```
   서비스 이름: Good Morning API HTTPS
   외부 포트: 443
   내부 포트: 443
   내부 IP: [현재 컴퓨터 IP]
   프로토콜: TCP
   ```

### **3단계: 현재 컴퓨터 IP 확인**

```powershell
# Windows에서 현재 컴퓨터의 로컬 IP 확인
ipconfig | findstr "IPv4"
# 예시 결과: 192.168.1.100
```

### **4단계: Windows 방화벽 설정**

```powershell
# PowerShell 관리자 권한으로 실행
# HTTP 포트 허용
netsh advfirewall firewall add rule name="Good Morning API HTTP" dir=in action=allow protocol=TCP localport=80

# HTTPS 포트 허용
netsh advfirewall firewall add rule name="Good Morning API HTTPS" dir=in action=allow protocol=TCP localport=443
```

### **5단계: 설정 확인**

1. **포트 포워딩 테스트**
   - 외부 네트워크(모바일 데이터 등)에서 접속 테스트
   - `http://goodmorningkr01.duckdns.org/api/docs` 접속

2. **로컬 테스트**
   - `http://localhost/api/docs` 접속 확인

## 🏢 **공유기별 설정 방법**

### **ipTIME 공유기**
1. 관리도구 → 고급설정 → NAT/라우터 관리 → 포트포워드 설정
2. 규칙 이름: `Good Morning API`
3. 외부포트: `80-80`, 내부포트: `80-80`
4. 내부 IP 주소: 현재 컴퓨터 IP

### **공유기 (KT, LG 등)**
1. 포트포워딩/가상서버 메뉴
2. 서비스 포트: `80`, `443`
3. 서버 IP: 현재 컴퓨터 IP

### **ASUS 공유기**
1. 고급설정 → WAN → 가상 서버/포트 포워딩
2. 서비스 이름: `Good Morning API`
3. 포트 범위: `80`, `443`
4. 로컬 IP: 현재 컴퓨터 IP

## 🔒 **보안 고려사항**

### **권장 설정**
1. **관리자 비밀번호 변경**: 공유기 기본 비밀번호 변경
2. **불필요한 포트 차단**: 80, 443 외 다른 포트는 차단
3. **정기적인 업데이트**: 공유기 펌웨어 업데이트

### **추가 보안**
```bash
# 특정 IP만 허용 (선택사항)
# Nginx 설정에서 allow/deny 지시어 사용
```

## 🆘 **문제 해결**

### **일반적인 문제들**

1. **여전히 공유기 페이지가 나타남**
   - 포트 포워딩 설정 재확인
   - 공유기 재부팅
   - DNS 캐시 초기화: `ipconfig /flushdns`

2. **내부에서는 되지만 외부에서 안됨**
   - 공유기 포트 포워딩 설정 확인
   - ISP 차단 여부 확인 (일부 ISP는 80번 포트 차단)

3. **간헐적 접속 불가**
   - 동적 IP 변경 확인
   - DuckDNS 자동 업데이트 설정

### **대안 방법**

1. **다른 포트 사용**
   ```yaml
   # docker-compose.yml에서 포트 변경
   ports:
     - "8080:80"  # 8080 포트 사용
   ```

2. **ngrok 사용 (임시 테스트용)**
   ```bash
   # ngrok 설치 후
   ngrok http 80
   ```

3. **클라우드 배포**
   - AWS, Google Cloud, Heroku 등 사용

## 📱 **모바일에서 테스트**

포트 포워딩 설정 후:
1. 모바일 데이터로 전환 (Wi-Fi 끄기)
2. `http://goodmorningkr01.duckdns.org/api/docs` 접속
3. API 문서가 정상적으로 로드되는지 확인

## 🎯 **성공 확인**

설정이 완료되면:
- ✅ 외부에서 `http://goodmorningkr01.duckdns.org/api/docs` 접속 가능
- ✅ API 문서 페이지 정상 로드
- ✅ WebSocket 테스트 페이지 접근 가능
- ✅ PgAdmin 관리 도구 접근 가능

---

**참고**: 일부 ISP(인터넷 서비스 제공업체)에서는 보안상의 이유로 80번 포트를 차단할 수 있습니다. 이 경우 8080 등 다른 포트를 사용하거나 클라우드 서비스를 이용하는 것을 권장합니다. 