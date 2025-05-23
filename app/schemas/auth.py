from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    token: str = Field(..., description="Firebase UID")

    class Config:
        schema_extra = {
            "example": {
                "token": "firebase_uid_here"
            }
        }

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(..., description="토큰 타입")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6...",
                "token_type": "bearer"
            }
        }

class TokenData(BaseModel):
    firebase_uid: str = Field(..., description="Firebase UID")
    email: str = Field(None, description="사용자 이메일")


    