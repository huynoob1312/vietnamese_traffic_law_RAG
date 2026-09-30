from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==========================================
# 1. Auth Schemas
# ==========================================

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập")
    password: str = Field(..., min_length=6, max_length=100, description="Mật khẩu tối thiểu 6 ký tự")


class UserLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 2. Chat & Citations Schemas
# ==========================================

class CitationItem(BaseModel):
    source: Optional[str] = None
    dieu: Optional[str] = None
    khoan: Optional[str] = None
    diem: Optional[str] = None
    page_content: Optional[str] = None


class ChatRequest(BaseModel):
    question: Optional[str] = None
    query: Optional[str] = None
    session_id: Optional[str] = None

    @property
    def prompt(self) -> str:
        return self.question or self.query or ""


class ChatResponse(BaseModel):
    answer: str
    citations: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None


# ==========================================
# 3. Session & History Schemas
# ==========================================

class SessionCreateRequest(BaseModel):
    title: Optional[str] = "Đoạn chat mới"


class SessionUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class MessageResponse(BaseModel):
    message_id: int
    session_id: str
    role: str
    content: str
    citations: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    session_id: str
    user_id: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    session_id: str
    user_id: int
    title: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True
