# API module 
from fastapi import APIRouter

router = APIRouter()

from . import routes
from . import db_check

# 라우터 포함
router.include_router(routes.router, tags=["users"])
router.include_router(db_check.router, tags=["database"]) 