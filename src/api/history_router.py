import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db.database import get_db
from src.db.models import User, ChatSession, ChatMessage
from src.api.dependencies import get_current_user
from src.api.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionDetailResponse,
    MessageResponse
)

router = APIRouter(prefix="/sessions", tags=["Chat History"])


@router.get("", response_model=List[SessionResponse])
def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách các phiên trò chuyện của người dùng hiện tại."""
    # Truy vấn phiên kèm đếm số lượng tin nhắn
    sessions_query = (
        db.query(
            ChatSession,
            func.count(ChatMessage.message_id).label("message_count")
        )
        .outerjoin(ChatMessage, ChatSession.session_id == ChatMessage.session_id)
        .filter(ChatSession.user_id == current_user.user_id)
        .group_by(ChatSession.session_id)
        .order_by(
            func.coalesce(ChatSession.updated_at, ChatSession.created_at).desc()
        )
        .all()
    )

    result = []
    for s, count in sessions_query:
        result.append(
            SessionResponse(
                session_id=s.session_id,
                user_id=s.user_id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=count
            )
        )
    return result


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    request: SessionCreateRequest = SessionCreateRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Khởi tạo một phiên trò chuyện mới."""
    new_session = ChatSession(
        session_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        title=request.title or "Đoạn chat mới"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return SessionResponse(
        session_id=new_session.session_id,
        user_id=new_session.user_id,
        title=new_session.title,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
        message_count=0
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy chi tiết phiên trò chuyện kèm toàn bộ tin nhắn và trích dẫn pháp lý."""
    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_id == session_id, ChatSession.user_id == current_user.user_id)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phiên trò chuyện không tồn tại hoặc bạn không có quyền truy cập"
        )

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return SessionDetailResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            MessageResponse(
                message_id=m.message_id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                citations=m.citations,
                created_at=m.created_at
            )
            for m in messages
        ]
    )


@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật tiêu đề phiên trò chuyện."""
    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_id == session_id, ChatSession.user_id == current_user.user_id)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phiên trò chuyện không tồn tại"
        )

    session.title = request.title.strip()
    db.commit()
    db.refresh(session)

    count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=count
    )


@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Xóa phiên trò chuyện và toàn bộ tin nhắn liên quan."""
    session = (
        db.query(ChatSession)
        .filter(ChatSession.session_id == session_id, ChatSession.user_id == current_user.user_id)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phiên trò chuyện không tồn tại"
        )

    db.delete(session)
    db.commit()
    return {"status": "success", "message": "Đã xóa phiên trò chuyện thành công"}
