from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from firebase_admin import auth
from app.models.models import User, Token, TokenData, SignupData, UserData, User as UserSchema
from app.models.database_models import User as UserModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from typing import Optional
from app.core.firebase import initialize_firebase
from app.core import get_settings
from app.models.database_models import User as models
from app.auth.utils import verify_token, get_current_user
import uuid
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import datetime

router = APIRouter()
settings = get_settings()
firebase_app = initialize_firebase()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None

@router.post("/google-auth")
async def google_auth(user_data: UserData, request: Request, db: Session = Depends(get_db)):
    try:
        # 구글에서 받은 ID 토큰 검증
        decoded_token = auth.verify_id_token(user_data.id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        # 현재 시간과 IP 주소 가져오기
        current_time = datetime.datetime.now()
        client_ip = request.client.host
        
        # 데이터베이스에서 사용자 확인
        db_user = db.query(UserModel).filter(UserModel.firebase_uid == uid).first()
        if db_user:
            # 사용자가 이미 존재함 - 마지막 로그인 시간 업데이트
            db_user.updated_at = current_time
            # 추가 필드가 있다면 여기서 업데이트 (last_login_at, last_login_ip 등)
            is_new_user = False
        else:
            # 사용자가 존재하지 않으면 새로 생성 (회원가입)
            db_user = UserModel(
                firebase_uid=uid,
                email=email,
                name=user_data.name or decoded_token.get('name', ''),
                is_active=True
                # 추가 필드가 있다면 여기서 설정
                # profile_picture=user_data.profile_picture
            )
            db.add(db_user)
            is_new_user = True
        
        # 변경사항 커밋
        db.commit()
        db.refresh(db_user)
        
        # 로그인 이력 기록 (LoginHistory 테이블이 있다면)
        # login_history = LoginHistory(
        #     user_id=db_user.id,
        #     login_time=current_time,
        #     ip_address=client_ip,
        #     device_info=request.headers.get('User-Agent', '')
        # )
        # db.add(login_history)
        # db.commit()
            
        return {
            "success": True,
            "user": {
                "uid": uid,
                "email": db_user.email,
                "displayName": db_user.name,
                "emailVerified": True
            },
            "isNewUser": is_new_user
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"인증 오류: {str(e)}")

@router.post("/protected-endpoint")
async def protected_endpoint(request: Request, data: Optional[SignupData] = None):
    # 요청 헤더에서 Authorization 헤더를 가져옵니다.
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # 'Bearer ' 부분을 제거하고 토큰만 추출합니다.
    try:
        id_token = auth_header.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        # Firebase ID 토큰 검증
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        # uid를 기반으로 유저를 식별하고 필요한 작업을 수행합니다.
        return {"message": "Token is valid", "uid": uid}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/signup")
async def signup(data: SignupData):
    # 여기서 데이터베이스에 유저 정보를 저장하거나 토큰을 검증하는 등의 작업을 수행합니다.
    print(f"Username: {data.username}, Name: {data.name}, Token: {data.token}")
    return {"message": "Signup successful"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Firebase Authentication을 통한 로그인
        user = firebase_app.auth().sign_in_with_email_and_password(
            form_data.username, form_data.password
        )
        return {
            "access_token": user["idToken"],
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=UserSchema)
async def register(user: UserSchema):
    try:
        # Firebase Authentication을 통한 회원가입
        user_record = firebase_app.auth().create_user(
            email=user.email,
            password=user.password,
            display_name=user.name
        )
        return UserSchema(
            id=user_record.uid,
            email=user.email,
            name=user.name
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/verify-token")
async def verify_auth_token(token_data: dict = Depends(verify_token)):
    """Firebase 토큰을 검증하고 사용자 정보를 반환합니다."""
    return {
        "firebase_uid": token_data["firebase_uid"],
        "email": token_data["email"],
        "name": token_data["name"]
    }

@router.post("/verify-token")
async def verify_auth_token_post(token_data: dict = Depends(verify_token)):
    """Firebase 토큰을 검증하고 사용자 정보를 반환합니다. (POST 메서드)"""
    return {
        "firebase_uid": token_data["firebase_uid"],
        "email": token_data["email"],
        "name": token_data["name"]
    }

@router.post("/register-with-token")
async def register_user_with_token(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """인증된 Firebase 사용자를 데이터베이스에 등록합니다."""
    # 이미 존재하는 사용자인지 확인
    existing_user = db.query(UserModel).filter(UserModel.firebase_uid == token_data["firebase_uid"]).first()
    if existing_user:
        return {
            "detail": "이미 등록된 사용자입니다",
            "user_id": str(existing_user.id)
        }
    
    # 새 사용자 생성
    new_user = UserModel(
        firebase_uid=token_data["firebase_uid"],
        email=token_data["email"],
        name=token_data["name"],
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "detail": "사용자 등록 완료",
        "user_id": str(new_user.id)
    }

@router.get("/check-users")
async def check_users(db: Session = Depends(get_db)):
    """데이터베이스에 사용자가 존재하는지 확인합니다."""
    users = db.query(UserModel).all()
    
    if not users:
        return {"exists": False, "count": 0, "message": "사용자 데이터가 없습니다."}
    
    return {
        "exists": True,
        "count": len(users),
        "users": [
            {
                "id": str(user.id),
                "firebase_uid": user.firebase_uid,
                "email": user.email,
                "name": user.name,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            for user in users[:5]  # 최대 5명의 사용자만 반환
        ]
    } 