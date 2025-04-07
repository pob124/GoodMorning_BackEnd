from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from firebase_admin import auth
from app.models.models import UserData, SignupData, Token, User
from typing import Optional
from app.core.firebase import initialize_firebase
from app.core import get_settings

router = APIRouter()
settings = get_settings()
firebase_app = initialize_firebase()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/google-auth")
async def google_auth(user_data: UserData):
    try:
        # 구글에서 받은 ID 토큰 검증
        decoded_token = auth.verify_id_token(user_data.id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        # 사용자가 이미 존재하는지 확인
        try:
            user = auth.get_user(uid)
            is_new_user = False
        except:
            # 사용자가 존재하지 않으면 새로 생성 (회원가입)
            user_properties = {
                'uid': uid,
                'email': email,
                'display_name': user_data.name or decoded_token.get('name', ''),
                'photo_url': user_data.profile_picture or decoded_token.get('picture', ''),
                'email_verified': decoded_token.get('email_verified', False)
            }
            user = auth.create_user(**user_properties)
            is_new_user = True
            
        return {
            "success": True,
            "user": {
                "uid": user.uid,
                "email": user.email,
                "displayName": user.display_name,
                "photoURL": user.photo_url,
                "emailVerified": user.email_verified
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

@router.post("/register", response_model=User)
async def register(user: User):
    try:
        # Firebase Authentication을 통한 회원가입
        user_record = firebase_app.auth().create_user(
            email=user.email,
            password=user.password,
            display_name=user.name
        )
        return User(
            id=user_record.uid,
            email=user.email,
            name=user.name
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 