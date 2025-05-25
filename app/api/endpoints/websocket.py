from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.firebase import get_current_user_id, get_db
from app.utils.utils import (
    get_chatroom_or_404, 
    verify_chatroom_participant, 
    create_message, 
    connection_manager
)
from app.schemas.websocket import (
    WebSocketIncomingMessage,
    AuthMessage,
    ChatMessage,
    ChatMessageResponse,
    UserStatusMessage,
    ErrorMessage,
    SuccessMessage,
    PongMessage,
    ActiveUsersResponse
)
import logging
import json
from datetime import datetime
from pydantic import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
    responses={
        101: {"description": "WebSocket Upgrade Successful"},
        400: {"description": "Bad Request"},
        401: {"description": "Unauthorized"},
        404: {"description": "Chatroom Not Found"},
        1008: {"description": "Policy Violation (Authentication failed)"},
        1011: {"description": "Internal Error"}
    }
)

async def send_websocket_message(websocket: WebSocket, message_obj):
    """WebSocket으로 구조화된 메시지 전송"""
    try:
        await websocket.send_text(message_obj.model_dump_json())
    except Exception as e:
        logger.error(f"Failed to send WebSocket message: {e}")

@router.get("/chat/{room_id}", summary="채팅방 WebSocket 연결")
async def get_websocket_info(room_id: str):
    """
    채팅방 WebSocket 연결 정보
    
    **실제 WebSocket 연결:**
    ```
    ws://localhost/api/ws/chat/{room_id}
    ```
    
    **인증 과정:**
    1. WebSocket 연결 수립
    2. 첫 번째 메시지로 JWT 토큰 전송: `{"type": "auth", "token": "YOUR_JWT_TOKEN"}`
    3. 인증 성공 후 실시간 채팅 가능
    
    **지원되는 메시지 타입:**
    - `auth`: 인증 (필수 - 첫 번째 메시지)
    - `ping`: 연결 상태 확인
    - `get_active_users`: 활성 사용자 목록 요청
    
    **응답 메시지 타입:**
    - `message_response`: 새로운 채팅 메시지 (REST API로 전송된 메시지의 실시간 알림)
    - `system`: 시스템 메시지 (입장/퇴장 알림)
    - `user_status`: 사용자 상태 변경
    - `error`: 오류 메시지
    - `success`: 성공 메시지
    - `pong`: ping에 대한 응답
    - `active_users_response`: 활성 사용자 목록
    
    **주의사항:**
    - 이 GET 엔드포인트는 문서화 목적입니다
    - 실제 WebSocket 연결은 `ws://` 프로토콜을 사용하세요
    - **메시지 전송은 POST /api/chat/{room_id}를 사용하세요**
    - WebSocket은 실시간 알림 수신 전용입니다
    """
    return {
        "endpoint": f"ws://localhost/api/ws/chat/{room_id}",
        "protocol": "WebSocket",
        "description": "실시간 채팅을 위한 WebSocket 엔드포인트",
        "auth_required": True,
        "auth_method": "첫 번째 메시지로 JWT 토큰 전송",
        "supported_message_types": [
            "auth", "ping", "get_active_users"
        ],
        "response_message_types": [
            "message_response", "system", "user_status", 
            "error", "success", "pong", "active_users_response"
        ],
        "example_messages": {
            "auth": {"type": "auth", "token": "YOUR_JWT_TOKEN"},
            "ping": {"type": "ping"},
            "get_users": {"type": "get_active_users"}
        },
        "note": "WebSocket 클라이언트를 사용하여 실제 연결을 테스트하세요"
    }

@router.websocket("/chat/{room_id}")
async def websocket_chat_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket 실시간 채팅 엔드포인트
    
    **연결 방법:**
    ```
    ws://localhost/api/ws/chat/{room_id}
    ```
    
    **인증:**
    첫 번째 메시지로 JWT 토큰을 포함한 인증 메시지를 보내야 합니다:
    ```json
    {"type": "auth", "token": "YOUR_JWT_TOKEN"}
    ```
    
    **지원되는 메시지 타입:**
    - `auth`: 인증 (필수 - 첫 번째 메시지)
    - `ping`: 연결 상태 확인 
    - `get_active_users`: 현재 활성 사용자 목록 요청
    
    **응답 메시지 타입:**
    - `message_response`: 새로운 채팅 메시지
    - `system`: 시스템 메시지 (입장/퇴장 알림)
    - `user_status`: 사용자 상태 변경
    - `error`: 오류 메시지
    - `success`: 성공 메시지
    - `pong`: ping에 대한 응답
    - `active_users_response`: 활성 사용자 목록
    
    **메시지 예시:**
    ```json
    // 연결 확인
    {"type": "ping"}
    
    // 활성 사용자 요청
    {"type": "get_active_users"}
    ```
    
    **연결 종료:**
    클라이언트가 연결을 종료하면 자동으로 채팅방에서 제거되며,
    다른 참여자들에게 퇴장 알림이 전송됩니다.
    
    Args:
        websocket (WebSocket): WebSocket 연결 객체
        room_id (str): 채팅방 ID
        
    Note:
        - 채팅방에 참여할 권한이 있는 사용자만 연결 가능
        - 모든 메시지는 JSON 형식이어야 함
        - 비정상적인 연결 종료 시 자동 정리됨
    """
    db = next(get_db())
    user_id = None
    authenticated = False
    
    try:
        # WebSocket 연결 수락
        await websocket.accept()
        
        # 연결 성공 메시지
        success_msg = SuccessMessage(
            message="WebSocket connection established. Please authenticate with first message.",
            timestamp=datetime.utcnow()
        )
        await send_websocket_message(websocket, success_msg)
        
        # 메시지 처리 루프
        while True:
            try:
                # 메시지 수신
                data = await websocket.receive_text()
                
                try:
                    # JSON 메시지 파싱
                    message_dict = json.loads(data)
                    message_type = message_dict.get("type")
                    
                    # 인증되지 않은 상태에서는 auth 메시지만 허용
                    if not authenticated:
                        if message_type != "auth":
                            error_msg = ErrorMessage(
                                code=1008,
                                message="Authentication required. Send auth message first.",
                                timestamp=datetime.utcnow()
                            )
                            await send_websocket_message(websocket, error_msg)
                            continue
                        
                        # 인증 처리
                        try:
                            auth_data = AuthMessage.model_validate(message_dict)
                            
                            # 토큰 검증
                            from app.core.firebase import auth
                            decoded_token = auth.verify_id_token(auth_data.token)
                            user_id = decoded_token["uid"]
                            logger.info(f"WebSocket authentication successful for user: {user_id}")
                            
                            # 채팅방 존재 여부 확인
                            chatroom = get_chatroom_or_404(db, room_id)
                            
                            # 참여자 확인
                            verify_chatroom_participant(chatroom, user_id)
                            
                            # 인증 성공
                            authenticated = True
                            
                            # WebSocket 연결 등록
                            await connection_manager.connect(websocket, room_id, user_id)
                            logger.info(f"User {user_id} connected to chatroom {room_id}")
                            
                            # 인증 성공 메시지
                            auth_success = SuccessMessage(
                                message=f"Authentication successful. Welcome to chatroom {room_id}!",
                                timestamp=datetime.utcnow()
                            )
                            await send_websocket_message(websocket, auth_success)
                            
                        except HTTPException as e:
                            error_msg = ErrorMessage(
                                code=1008,
                                message=f"Authentication failed: {e.detail}",
                                timestamp=datetime.utcnow()
                            )
                            await send_websocket_message(websocket, error_msg)
                            await websocket.close(code=1008)
                            return
                            
                        except Exception as e:
                            logger.error(f"WebSocket authentication failed: {str(e)}")
                            error_msg = ErrorMessage(
                                code=1008,
                                message="Invalid authentication",
                                details=str(e),
                                timestamp=datetime.utcnow()
                            )
                            await send_websocket_message(websocket, error_msg)
                            await websocket.close(code=1008)
                            return
                        
                        continue
                    
                    # 인증된 후 메시지 타입별 처리
                    if message_type == "message":
                        # 메시지 전송은 REST API(/api/chat/{room_id})를 사용하도록 안내
                        error_msg = ErrorMessage(
                            code=400,
                            message="Message sending via WebSocket is deprecated. Use POST /api/chat/{room_id} instead.",
                            details="WebSocket is for real-time notifications only. Send messages via REST API for better reliability.",
                            timestamp=datetime.utcnow()
                        )
                        await send_websocket_message(websocket, error_msg)
                        
                    elif message_type == "ping":
                        # Ping 응답
                        pong_msg = PongMessage(timestamp=datetime.utcnow())
                        await send_websocket_message(websocket, pong_msg)
                        
                    elif message_type == "get_active_users":
                        # 활성 사용자 목록 요청
                        active_users = connection_manager.get_active_users(room_id)
                        users_response = ActiveUsersResponse(
                            users=active_users,
                            timestamp=datetime.utcnow()
                        )
                        await send_websocket_message(websocket, users_response)
                        
                    else:
                        # 지원하지 않는 메시지 타입
                        error_msg = ErrorMessage(
                            code=400,
                            message=f"Unsupported message type: {message_type}",
                            timestamp=datetime.utcnow()
                        )
                        await send_websocket_message(websocket, error_msg)
                        
                except ValidationError as e:
                    # 스키마 검증 실패
                    error_msg = ErrorMessage(
                        code=400,
                        message="Invalid message format",
                        details=str(e),
                        timestamp=datetime.utcnow()
                    )
                    await send_websocket_message(websocket, error_msg)
                    
                except json.JSONDecodeError:
                    # JSON 파싱 실패
                    if authenticated:
                        # 인증된 사용자는 일반 텍스트도 허용
                        if data.strip():
                            db_message = create_message(db, data, room_id, user_id)
                            logger.info(f"Text message saved: {db_message.id} from {user_id}")
                            
                            response_msg = ChatMessageResponse(
                                id=str(db_message.id),
                                sender_id=db_message.sender_id,
                                content=db_message.content,
                                timestamp=db_message.timestamp
                            )
                            await connection_manager.broadcast_structured_message(response_msg, room_id)
                    else:
                        error_msg = ErrorMessage(
                            code=400,
                            message="Authentication required. Send JSON auth message first.",
                            timestamp=datetime.utcnow()
                        )
                        await send_websocket_message(websocket, error_msg)
                        
            except WebSocketDisconnect:
                # 연결 종료 처리
                disconnected_user = connection_manager.disconnect(websocket, room_id)
                if disconnected_user:
                    logger.info(f"User {disconnected_user} disconnected from chatroom {room_id}")
                    
                    # 퇴장 알림 메시지
                    user_left_msg = UserStatusMessage(
                        user_id=disconnected_user,
                        status="left",
                        content=f"User {disconnected_user} left the chat",
                        timestamp=datetime.utcnow()
                    )
                    await connection_manager.broadcast_structured_message(user_left_msg, room_id)
                break
    
    except Exception as e:
        # 예상치 못한 오류 처리
        logger.error(f"WebSocket error: {str(e)}")
        try:
            if user_id and authenticated:
                connection_manager.disconnect(websocket, room_id)
            
            error_msg = ErrorMessage(
                code=1011,
                message="Server error",
                details=str(e),
                timestamp=datetime.utcnow()
            )
            await send_websocket_message(websocket, error_msg)
            await websocket.close(code=1011)
        except:
            pass
    finally:
        # DB 세션 정리
        try:
            db.close()
        except:
            pass 

@router.get("/status/{room_id}", summary="WebSocket 연결 상태 확인 (관리자용)")
async def get_websocket_status(room_id: str):
    """
    특정 채팅방의 WebSocket 연결 상태 확인 (관리자/디버깅용)
    
    **chat.py의 active-users와의 차이점:**
    - 이 엔드포인트: 인증 불필요, WebSocket 연결 상태 정보 포함
    - chat.py active-users: 인증 필요, 단순 사용자 목록만
    
    **용도:**
    - 서버 관리 및 디버깅
    - WebSocket 연결 상태 모니터링
    - 시스템 상태 확인
    
    현재 채팅방에 연결된 WebSocket 연결 수와 상세 정보를 반환합니다.
    """
    active_users = connection_manager.get_active_users(room_id)
    connection_count = len(active_users)
    
    return {
        "room_id": room_id,
        "websocket_connections": connection_count,
        "connected_users": active_users,
        "connection_status": "active" if connection_count > 0 else "inactive",
        "timestamp": datetime.utcnow(),
        "note": "이 엔드포인트는 WebSocket 연결 상태 확인용입니다. 일반 사용자는 /api/chat/{room_id}/active-users를 사용하세요."
    }

@router.get("/status", summary="전체 WebSocket 연결 상태 (관리자용)")
async def get_all_websocket_status():
    """
    모든 채팅방의 WebSocket 연결 상태 확인 (관리자/디버깅용)
    
    **용도:**
    - 서버 전체 WebSocket 연결 모니터링
    - 시스템 부하 확인
    - 디버깅 및 관리
    
    현재 활성화된 모든 채팅방과 WebSocket 연결 정보를 반환합니다.
    """
    all_connections = {}
    total_connections = 0
    
    for room_id, users in connection_manager.active_connections.items():
        user_list = list(users.keys())
        all_connections[room_id] = {
            "websocket_connections": len(user_list),
            "connected_users": user_list
        }
        total_connections += len(user_list)
    
    return {
        "total_websocket_connections": total_connections,
        "active_rooms": len(all_connections),
        "rooms": all_connections,
        "timestamp": datetime.utcnow(),
        "note": "이 엔드포인트는 시스템 관리용입니다."
    } 