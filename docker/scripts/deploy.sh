#!/bin/bash

# Good Morning API 배포 스크립트

set -e

echo "🚀 Good Morning API 배포 시작..."

# 환경 변수 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다. env.example을 참고하여 생성해주세요."
    exit 1
fi

# Docker 및 Docker Compose 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

# 기존 컨테이너 중지 및 제거
echo "🛑 기존 컨테이너 중지 중..."
docker-compose down

# 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker-compose build --no-cache

# 서비스 시작
echo "▶️ 서비스 시작 중..."
docker-compose up -d

# 서비스 상태 확인
echo "🔍 서비스 상태 확인 중..."
sleep 10
docker-compose ps

# 헬스 체크
echo "🏥 헬스 체크 중..."
if curl -f http://localhost/api/docs > /dev/null 2>&1; then
    echo "✅ 배포 성공! API 문서: http://localhost/api/docs"
else
    echo "❌ 헬스 체크 실패. 로그를 확인해주세요:"
    docker-compose logs web
    exit 1
fi

echo "🎉 배포 완료!" 