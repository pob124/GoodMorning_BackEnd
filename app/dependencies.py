from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.firebase import verify_token, get_db
from app.models.user_models import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    decoded_token = verify_token(token)
    if decoded_token is None:
        raise credentials_exception
        
    token_data = TokenData(firebase_uid=decoded_token.get("uid"))
    if token_data.firebase_uid is None:
        raise credentials_exception
        
    return token_data 