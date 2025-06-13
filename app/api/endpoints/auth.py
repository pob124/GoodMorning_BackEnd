from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from app.core.firebase import verify_token, get_db, auth
from app.models.user_models import TokenData, UserDB
from sqlalchemy.orm import Session
import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["인증"])

@router.post("/login")
async def login(
    request_data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Firebase UID를 사용하여 커스텀 토큰을 생성합니다."""
    try:
        uid = request_data.get("uid")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="UID is required"
            )
        
        # Firebase 커스텀 토큰 생성
        custom_token = auth.create_custom_token(uid)
        
        # 바이트를 문자열로 변환
        if isinstance(custom_token, bytes):
            custom_token = custom_token.decode('utf-8')
        
        logger.info(f"Custom token created for UID: {uid}")
        
        return {
            "access_token": custom_token,
            "token_type": "bearer",
            "uid": uid
        }
    except Exception as e:
        logger.error(f"Failed to create custom token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom token: {str(e)}"
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    decoded_token = await verify_token(token)
    if not decoded_token or "uid" not in decoded_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    print("decode 성공")
    return TokenData(firebase_uid=decoded_token["uid"])



@router.post("/sync")
async def sync_user(
    token_data: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = token_data.firebase_uid
    firebase_user = auth.get_user(uid)

    # Firebase 사용자 정보 로깅
    logger.info(f"Firebase user info for UID {uid}:")
    logger.info(f"  - Email: {firebase_user.email}")
    logger.info(f"  - Display Name: {firebase_user.display_name}")
    logger.info(f"  - Photo URL: {firebase_user.photo_url}")
    logger.info(f"  - Phone Number: {firebase_user.phone_number}")
    logger.info(f"  - Provider Data: {firebase_user.provider_data}")

    db_user = db.query(UserDB).filter_by(firebase_uid=uid).first()
    if not db_user:
        # 새 사용자 생성 시 모든 Firebase 정보 저장
        db_user = UserDB(
            firebase_uid=uid,
            email=firebase_user.email or "",
            name=firebase_user.display_name or "",
            profile_picture=firebase_user.photo_url,  # 프로필 이미지 URL 저장
            phone_number=firebase_user.phone_number
        )
        db.add(db_user)
        logger.info(f"Created new user with profile_picture: {firebase_user.photo_url}")
    else:
        # 기존 사용자 정보 업데이트 (프로필 이미지가 비어있을 경우에만)
        updated = False
        if not db_user.profile_picture and firebase_user.photo_url:
            db_user.profile_picture = firebase_user.photo_url
            updated = True
            logger.info(f"Updated existing user profile_picture: {firebase_user.photo_url}")
        
        if firebase_user.display_name and db_user.name != firebase_user.display_name:
            db_user.name = firebase_user.display_name
            updated = True
            
        if updated:
            logger.info(f"Updated user info for UID {uid}")
    
    db.commit()
    db.refresh(db_user)

    return {
        "success": True, 
        "uid": uid,
        "profile_picture": db_user.profile_picture,
        "display_name": db_user.name
    }
