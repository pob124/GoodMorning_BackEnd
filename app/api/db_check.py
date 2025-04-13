from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database_models import User as models
from app.core.database import get_db
from sqlalchemy import text
from typing import List

router = APIRouter()

@router.get("/db-check")
async def db_check(db: Session = Depends(get_db)):
    """데이터베이스 연결 상태를 확인합니다."""
    try:
        # 간단한 쿼리 실행
        result = db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            # 사용자 테이블 확인
            users = db.query(models).limit(5).all()
            return {
                "status": "connected",
                "database": "PostgreSQL",
                "tables": {
                    "users": {
                        "count": len(users),
                        "sample": [
                            {
                                "id": str(user.id),
                                "email": user.email,
                                "is_active": user.is_active
                            } for user in users
                        ] if users else []
                    }
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 연결 오류: {str(e)}"
        ) 