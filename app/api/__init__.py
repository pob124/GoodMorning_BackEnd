# API module 
from fastapi import APIRouter
from app.api.endpoints import auth, users, chatrooms, chat, websocket, admin

router = APIRouter()

# API 엔드포인트 라우터 등록
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(chatrooms.router)
router.include_router(chat.router)
router.include_router(websocket.router)
router.include_router(admin.router) 