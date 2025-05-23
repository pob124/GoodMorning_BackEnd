from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from app.core.firebase import verify_token, get_db, auth
from app.models.user_models import Token, TokenData, UserDB
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["인증"])

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

    db_user = db.query(UserDB).filter_by(firebase_uid=uid).first()
    if not db_user:
        db_user = UserDB(
            firebase_uid=uid,
            email=firebase_user.email or "",
            name=firebase_user.display_name or ""
        )
        db.add(db_user)
        db.commit()

    return {"success": True, "uid": uid}
