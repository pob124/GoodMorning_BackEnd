# Good Morning API 프로덕션 배포 스크립트 (Windows PowerShell)

Write-Host "🚀 Good Morning API 프로덕션 배포 시작..." -ForegroundColor Green
Write-Host "📍 도메인: goodmorningkr01.duckdns.org" -ForegroundColor Cyan

# 환경 변수 파일 확인
if (-not (Test-Path "configs/env.production")) {
    Write-Host "❌ configs/env.production 파일이 없습니다." -ForegroundColor Red
    Write-Host "📝 configs/env.production 파일을 생성하고 다음 값들을 설정해주세요:" -ForegroundColor Yellow
    Write-Host "   - POSTGRES_PASSWORD (강력한 비밀번호)" -ForegroundColor Yellow
    Write-Host "   - PGADMIN_PASSWORD (PgAdmin 비밀번호)" -ForegroundColor Yellow
    Write-Host "   - SSL_EMAIL (Let's Encrypt용 이메일)" -ForegroundColor Yellow
    exit 1
}

# .env 파일로 복사
Write-Host "📋 환경변수 파일 복사 중..." -ForegroundColor Yellow
Copy-Item "configs/env.production" ".env" -Force

# Docker 및 Docker Compose 확인
try {
    docker --version | Out-Null
    Write-Host "✅ Docker 확인됨" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker가 설치되어 있지 않습니다." -ForegroundColor Red
    exit 1
}

try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose 확인됨" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose가 설치되어 있지 않습니다." -ForegroundColor Red
    exit 1
}

# 기존 컨테이너 중지
Write-Host "🛑 기존 컨테이너 중지 중..." -ForegroundColor Yellow
try {
    docker-compose -f docker-compose.prod.yml down 2>$null
} catch {
    # 무시 (컨테이너가 없을 수 있음)
}

# 필요한 디렉토리 생성
Write-Host "📁 필요한 디렉토리 생성 중..." -ForegroundColor Yellow
if (-not (Test-Path "nginx/www")) {
    New-Item -ItemType Directory -Path "nginx/www" -Force | Out-Null
}

# 임시 HTTP 서버 시작 (Let's Encrypt 인증용)
Write-Host "🌐 임시 HTTP 서버 시작 중..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml up -d nginx

# Let's Encrypt 인증서 발급
Write-Host "🔒 SSL 인증서 발급 중..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
docker-compose -f docker-compose.prod.yml run --rm certbot

# SSL 설정으로 전환
Write-Host "🔄 SSL 설정으로 전환 중..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml down
Copy-Item "nginx/conf.d/ssl.conf" "nginx/conf.d/default.conf" -Force

# 프로덕션 서비스 시작
Write-Host "▶️ 프로덕션 서비스 시작 중..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d

# 서비스 상태 확인
Write-Host "🔍 서비스 상태 확인 중..." -ForegroundColor Yellow
Start-Sleep -Seconds 15
docker-compose -f docker-compose.prod.yml ps

# 헬스 체크
Write-Host "🏥 헬스 체크 중..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://goodmorningkr01.duckdns.org/api/docs" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ HTTPS 배포 성공!" -ForegroundColor Green
        Write-Host "🌐 API 문서: https://goodmorningkr01.duckdns.org/api/docs" -ForegroundColor Cyan
        Write-Host "🔧 PgAdmin: https://goodmorningkr01.duckdns.org/pgadmin/" -ForegroundColor Cyan
    }
} catch {
    try {
        $response = Invoke-WebRequest -Uri "http://goodmorningkr01.duckdns.org/api/docs" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "⚠️ HTTP로 접근 가능 (SSL 설정 확인 필요)" -ForegroundColor Yellow
            Write-Host "🌐 API 문서: http://goodmorningkr01.duckdns.org/api/docs" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "❌ 헬스 체크 실패. 로그를 확인해주세요:" -ForegroundColor Red
        docker-compose -f docker-compose.prod.yml logs web
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 배포 완료!" -ForegroundColor Green
Write-Host "📋 접속 정보:" -ForegroundColor Cyan
Write-Host "   - API 문서: https://goodmorningkr01.duckdns.org/api/docs" -ForegroundColor White
Write-Host "   - WebSocket 테스트: https://goodmorningkr01.duckdns.org/static/websocket_test.html" -ForegroundColor White
Write-Host "   - PgAdmin: https://goodmorningkr01.duckdns.org/pgadmin/" -ForegroundColor White
Write-Host ""
Write-Host "🔧 관리 명령어:" -ForegroundColor Cyan
Write-Host "   - 로그 확인: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
Write-Host "   - 서비스 재시작: docker-compose -f docker-compose.prod.yml restart" -ForegroundColor White
Write-Host "   - 서비스 중지: docker-compose -f docker-compose.prod.yml down" -ForegroundColor White 