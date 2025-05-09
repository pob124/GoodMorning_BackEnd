from firebase_admin import auth
from fastapi import HTTPException
from app.models.user import User
from sqlalchemy.orm import Session

class AuthService:
    @staticmethod
    async def verify_firebase_token(token: str, db: Session):
        try:
            # Firebase 토큰 검증
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']
            email = decoded_token.get('email')

            # DB에서 사용자 확인 또는 생성
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(
                    id=user_id,
                    email=email,
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            return user
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials") 