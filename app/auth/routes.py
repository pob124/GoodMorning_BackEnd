from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from firebase_admin import auth
from app.models.models import UserData, SignupData, Token, User as UserSchema
from app.models.database_models import User as UserModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from typing import Optional
from app.core.firebase import initialize_firebase
from app.core import get_settings
from app.api import schemas, models
from app.auth.utils import verify_token, get_current_user
import uuid

router = APIRouter()
settings = get_settings()
firebase_app = initialize_firebase()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/google-auth")
async def google_auth(user_data: UserData, db: Session = Depends(get_db)):
    try:
        # 구글에서 받은 ID 토큰 검증
        decoded_token = auth.verify_id_token(user_data.id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        # 데이터베이스에서 사용자 확인
        db_user = db.query(UserModel).filter(UserModel.firebase_uid == uid).first()
        if db_user:
            # 사용자가 이미 존재함
            is_new_user = False
        else:
            # 사용자가 존재하지 않으면 새로 생성 (회원가입)
            db_user = UserModel(
                firebase_uid=uid,
                email=email,
                name=user_data.name or decoded_token.get('name', ''),
                is_active=True
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            is_new_user = True
            
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

@router.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.post("/users/me", response_model=schemas.User)
async def update_users_me(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 현재 사용자 정보 업데이트
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.delete("/users/me", status_code=204)
async def delete_users_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 사용자 계정 비활성화 (또는 삭제)
    current_user.is_active = False
    db.commit()
    return {"detail": "User account deactivated"}

@router.post("/verify-token")
async def verify_auth_token(token_data: dict = Depends(verify_token)):
    """Firebase 토큰을 검증하고 사용자 정보를 반환합니다."""
    return {
        "firebase_uid": token_data["firebase_uid"],
        "email": token_data["email"],
        "name": token_data["name"]
    }

@router.post("/register")
async def register_user(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
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