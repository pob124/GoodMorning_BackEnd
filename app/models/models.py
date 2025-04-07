from pydantic import BaseModel, EmailStr
from typing import Optional

class UserData(BaseModel):
    id_token: str
    name: str = None
    profile_picture: str = None

class SignupData(BaseModel):
    username: str
    password: str
    name: str
    token: str

class User(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    is_active: bool = True
    password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 