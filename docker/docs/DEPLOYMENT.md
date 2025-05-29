# 🌐 Good Morning API 인터넷 배포 가이드

## 📋 배포 방법 비교

| 방법 | 비용 | 난이도 | 확장성 | 관리 편의성 |
|------|------|--------|--------|-------------|
| **AWS ECS** | 중간 | 중간 | 높음 | 높음 |
| **Google Cloud Run** | 낮음 | 쉬움 | 높음 | 높음 |
| **Heroku** | 중간 | 쉬움 | 중간 | 높음 |
| **DigitalOcean** | 낮음 | 중간 | 중간 | 중간 |
| **Railway** | 낮음 | 쉬움 | 중간 | 높음 |

## 🚀 **1. Google Cloud Run 배포 (권장)**

### 장점
- 서버리스 (사용한 만큼만 과금)
- 자동 스케일링
- 간단한 배포 과정

### 배포 단계
```bash
# 1. gcloud CLI 설치 및 로그인
gcloud auth login
gcloud config set project [프로젝트ID]

# 2. 프로젝트 빌드 및 배포
gcloud builds submit --tag gcr.io/[프로젝트ID]/goodmorning-api
gcloud run deploy goodmorning-api \
  --image gcr.io/[프로젝트ID]/goodmorning-api \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars="DEBUG=False,CORS_ORIGINS=*"

# 3. 데이터베이스 연결 (Cloud SQL)
gcloud sql instances create goodmorning-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=asia-northeast1

# 4. 환경변수 설정
gcloud run services update goodmorning-api \
  --set-env-vars="DATABASE_URL=postgresql://user:pass@/db?host=/cloudsql/project:region:instance"
```

## 🔧 **2. AWS ECS 배포**

### 사전 준비
```bash
# AWS CLI 설치 및 설정
aws configure
```

### 배포 단계
```bash
# 1. ECR 리포지토리 생성
aws ecr create-repository --repository-name goodmorning-api

# 2. Docker 이미지 빌드 및 푸시
$(aws ecr get-login --no-include-email --region ap-northeast-2)
docker build -t goodmorning-api .
docker tag goodmorning-api:latest [계정ID].dkr.ecr.ap-northeast-2.amazonaws.com/goodmorning-api:latest
docker push [계정ID].dkr.ecr.ap-northeast-2.amazonaws.com/goodmorning-api:latest

# 3. ECS 클러스터 및 서비스 생성 (AWS 콘솔에서)
```

## 💻 **3. VPS 배포 (DigitalOcean)**

### 서버 설정
```bash
# 1. Droplet 생성 (Ubuntu 20.04, 1GB RAM)

# 2. SSH 접속 후 초기 설정
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose git -y
sudo usermod -aG docker $USER

# 3. 프로젝트 클론 및 배포
git clone https://github.com/your-repo/GoodMorning_BackEnd.git
cd GoodMorning_BackEnd/docker
cp env.example .env
# .env 파일 수정 (도메인, 비밀번호 등)
chmod +x deploy.sh
./deploy.sh
```

### 도메인 및 SSL 설정
```bash
# 1. 도메인 DNS 설정
# A 레코드: api.yourdomain.com -> [서버IP]

# 2. SSL 인증서 발급
docker-compose -f docker-compose.prod.yml up certbot
docker-compose -f docker-compose.prod.yml up -d
```

## 🎯 **4. Heroku 배포**

### 배포 단계
```bash
# 1. Heroku CLI 설치 및 로그인
heroku login

# 2. 앱 생성 및 배포
heroku create goodmorning-api
heroku stack:set container
heroku addons:create heroku-postgresql:hobby-dev

# 3. 환경변수 설정
heroku config:set DEBUG=False
heroku config:set CORS_ORIGINS=*

# 4. 배포
git push heroku main
```

## 🚄 **5. Railway 배포**

### 배포 단계
```bash
# 1. Railway CLI 설치
npm install -g @railway/cli

# 2. 로그인 및 배포
railway login
railway init
railway add postgresql
railway up
```

## 🔒 **보안 설정**

### 환경변수 설정
```bash
# 프로덕션 환경변수
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
POSTGRES_PASSWORD=your_strong_password_here
PGADMIN_PASSWORD=your_admin_password_here
```

### 방화벽 설정
```bash
# Ubuntu UFW 설정
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

## 📊 **모니터링 설정**

### 로그 확인
```bash
# Docker 로그
docker-compose logs -f web

# 시스템 리소스 모니터링
docker stats
```

### 헬스 체크
```bash
# API 상태 확인
curl https://yourdomain.com/api/docs

# 데이터베이스 연결 확인
curl https://yourdomain.com/api/db-check
```

## 🔄 **CI/CD 설정**

### GitHub Actions 예시
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.4
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd GoodMorning_BackEnd/docker
          git pull origin main
          ./deploy.sh
```

## 📞 **문제 해결**

### 일반적인 문제들
1. **포트 접근 불가**: 방화벽 설정 확인
2. **SSL 인증서 오류**: Let's Encrypt 갱신 확인
3. **데이터베이스 연결 실패**: 환경변수 및 네트워크 설정 확인
4. **메모리 부족**: 서버 사양 업그레이드 또는 최적화

### 로그 확인 명령어
```bash
# 서비스 로그
docker-compose logs -f web

# 시스템 로그
sudo journalctl -u docker

# Nginx 로그
docker-compose exec nginx tail -f /var/log/nginx/error.log
``` 