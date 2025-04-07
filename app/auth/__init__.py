# Authentication module 

from fastapi import APIRouter

router = APIRouter()

from .routes import router
from .utils import get_current_user

__all__ = ["router", "get_current_user"] 