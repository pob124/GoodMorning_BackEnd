#!/bin/bash

# Good Morning API 프로덕션 배포 스크립트 (DuckDNS)

set -e

echo "🚀 Good Morning API 프로덕션 배포 시작..."
echo "📍 도메인: goodmorningkr01.duckdns.org"

# 환경 변수 파일 확인
if [ ! -f env.production ]; then
    echo "❌ env.production 파일이 없습니다."
    echo "📝 env.production 파일을 생성하고 다음 값들을 설정해주세요:"
    echo "   - POSTGRES_PASSWORD (강력한 비밀번호)"
    echo "   - PGADMIN_PASSWORD (PgAdmin 비밀번호)"
    echo "   - SSL_EMAIL (Let's Encrypt용 이메일)"
    exit 1
fi

# .env 파일로 복사
cp env.production .env

# Docker 및 Docker Compose 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

# 기존 컨테이너 중지
echo "🛑 기존 컨테이너 중지 중..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# 필요한 디렉토리 생성
echo "📁 필요한 디렉토리 생성 중..."
mkdir -p nginx/www

# 임시 HTTP 서버 시작 (Let's Encrypt 인증용)
echo "🌐 임시 HTTP 서버 시작 중..."
docker-compose -f docker-compose.yml up -d nginx

# Let's Encrypt 인증서 발급
echo "🔒 SSL 인증서 발급 중..."
sleep 5
docker-compose -f docker-compose.prod.yml run --rm certbot

# SSL 설정으로 전환
echo "🔄 SSL 설정으로 전환 중..."
docker-compose -f docker-compose.yml down
cp nginx/conf.d/ssl.conf nginx/conf.d/default.conf

# 프로덕션 서비스 시작
echo "▶️ 프로덕션 서비스 시작 중..."
docker-compose -f docker-compose.prod.yml up -d

# 서비스 상태 확인
echo "🔍 서비스 상태 확인 중..."
sleep 15
docker-compose -f docker-compose.prod.yml ps

# 헬스 체크
echo "🏥 헬스 체크 중..."
if curl -f https://goodmorningkr01.duckdns.org/api/docs > /dev/null 2>&1; then
    echo "✅ HTTPS 배포 성공!"
    echo "🌐 API 문서: https://goodmorningkr01.duckdns.org/api/docs"
    echo "🔧 PgAdmin: https://goodmorningkr01.duckdns.org/pgladmin/"
elif curl -f http://goodmorningkr01.duckdns.org/api/docs > /dev/null 2>&1; then
    echo "⚠️ HTTP로 접근 가능 (SSL 설정 확인 필요)"
    echo "🌐 API 문서: http://goodmorningkr01.duckdns.org/api/docs"
else
    echo "❌ 헬스 체크 실패. 로그를 확인해주세요:"
    docker-compose -f docker-compose.prod.yml logs web
    exit 1
fi

echo ""
echo "🎉 배포 완료!"
echo "📋 접속 정보:"
echo "   - API 문서: https://goodmorningkr01.duckdns.org/api/docs"
echo "   - WebSocket 테스트: https://goodmorningkr01.duckdns.org/static/websocket_test.html"
echo "   - PgAdmin: https://goodmorningkr01.duckdns.org/pgadmin/"
echo ""
echo "🔧 관리 명령어:"
echo "   - 로그 확인: docker-compose -f docker-compose.prod.yml logs -f"
echo "   - 서비스 재시작: docker-compose -f docker-compose.prod.yml restart"
echo "   - 서비스 중지: docker-compose -f docker-compose.prod.yml down" 