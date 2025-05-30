from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.firebase import get_db, get_current_user_id
from app.utils.init_data import create_default_chatrooms
from app.models.chatroom import ChatroomDB
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["관리자"],
    responses={404: {"description": "Not found"}},
)

@router.post("/chatrooms/create-defaults", status_code=201)
async def create_default_chatrooms_endpoint(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """관리자 권한으로 기본 채팅방들을 생성합니다."""
    
    # TODO: 실제 운영에서는 관리자 권한 체크 로직 추가
    # if not is_admin(current_user_id):
    #     raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    
    try:
        # 기존 시스템 채팅방 개수 확인
        existing_count = db.query(ChatroomDB).filter(
            ChatroomDB.created_by == 'system'
        ).count()
        
        if existing_count > 0:
            return {
                "message": f"기본 채팅방이 이미 {existing_count}개 존재합니다.",
                "existing_count": existing_count,
                "action": "skipped"
            }
        
        # 기본 채팅방 생성
        create_default_chatrooms(db)
        
        # 생성된 채팅방 개수 확인
        new_count = db.query(ChatroomDB).filter(
            ChatroomDB.created_by == 'system'
        ).count()
        
        logger.info(f"관리자 {current_user_id}에 의해 기본 채팅방 {new_count}개가 생성되었습니다.")
        
        return {
            "message": f"기본 채팅방 {new_count}개가 성공적으로 생성되었습니다.",
            "created_count": new_count,
            "action": "created"
        }
        
    except Exception as e:
        logger.error(f"기본 채팅방 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기본 채팅방 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/chatrooms/remove-defaults", status_code=200)
async def remove_default_chatrooms_endpoint(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """관리자 권한으로 시스템이 생성한 기본 채팅방들을 삭제합니다."""
    
    # TODO: 실제 운영에서는 관리자 권한 체크 로직 추가
    # if not is_admin(current_user_id):
    #     raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    
    try:
        # 시스템 채팅방들 조회
        system_chatrooms = db.query(ChatroomDB).filter(
            ChatroomDB.created_by == 'system'
        ).all()
        
        if not system_chatrooms:
            return {
                "message": "삭제할 시스템 채팅방이 없습니다.",
                "deleted_count": 0,
                "action": "skipped"
            }
        
        deleted_count = len(system_chatrooms)
        
        # 시스템 채팅방들 삭제
        for chatroom in system_chatrooms:
            db.delete(chatroom)
        
        db.commit()
        
        logger.info(f"관리자 {current_user_id}에 의해 시스템 채팅방 {deleted_count}개가 삭제되었습니다.")
        
        return {
            "message": f"시스템 채팅방 {deleted_count}개가 성공적으로 삭제되었습니다.",
            "deleted_count": deleted_count,
            "action": "deleted"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"시스템 채팅방 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 채팅방 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/chatrooms/system-stats", status_code=200)
async def get_system_chatrooms_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """시스템 채팅방 통계를 조회합니다."""
    
    try:
        # 시스템 채팅방 통계
        total_system_chatrooms = db.query(ChatroomDB).filter(
            ChatroomDB.created_by == 'system'
        ).count()
        
        active_system_chatrooms = db.query(ChatroomDB).filter(
            ChatroomDB.created_by == 'system',
            ChatroomDB.is_active == True
        ).count()
        
        inactive_system_chatrooms = total_system_chatrooms - active_system_chatrooms
        
        # 전체 채팅방 통계 (비교용)
        total_chatrooms = db.query(ChatroomDB).count()
        user_created_chatrooms = total_chatrooms - total_system_chatrooms
        
        return {
            "system_chatrooms": {
                "total": total_system_chatrooms,
                "active": active_system_chatrooms,
                "inactive": inactive_system_chatrooms
            },
            "total_chatrooms": total_chatrooms,
            "user_created_chatrooms": user_created_chatrooms,
            "timestamp": logger.handlers[0].formatter.formatTime(
                logging.LogRecord("", 0, "", 0, "", (), None)
            ) if logger.handlers else None
        }
        
    except Exception as e:
        logger.error(f"시스템 채팅방 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}"
        ) 