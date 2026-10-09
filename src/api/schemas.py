from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


# ==========================================
# 1. Auth Schemas
# ==========================================

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập")
    password: str = Field(..., min_length=6, max_length=100, description="Mật khẩu tối thiểu 6 ký tự")


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str
    user: Optional[UserResponse] = None


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


# ==========================================
# 3. Admin & System Management Schemas
# ==========================================

class QdrantConfig(BaseModel):
    collection_name: str


class ModelsConfig(BaseModel):
    embedding: str
    llm: str


class ChunkingConfig(BaseModel):
    thresh_dieu: int = Field(..., gt=0, description="Kích thước điều (phải là số nguyên > 0)")
    thresh_khoan_default: int = Field(..., gt=0, description="Kích thước khoản mặc định (> 0)")
    min_chunk: int = Field(..., gt=0, description="Kích thước chunk tối thiểu (> 0)")
    min_chunk_diem: int = Field(..., gt=0, description="Kích thước điểm tối thiểu (> 0)")


class RetrievalConfig(BaseModel):
    search_type: str = Field("hybrid", pattern="^(hybrid|bm25|vector)$")
    top_k: int = Field(..., gt=0, le=50, description="Số kết quả lấy ra (1 - 50)")
    use_reranker: bool = False
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    top_k_raw: int = Field(..., gt=0, description="Số kết quả thô ban đầu (> 0)")


class LLMParamsConfig(BaseModel):
    provider: str = Field(..., pattern="^(gemini|ollama)$")
    model: str = Field(..., min_length=1)
    temperature: Optional[float] = 0.1


class AppConfigResponse(BaseModel):
    qdrant: QdrantConfig
    models: ModelsConfig
    chunking: ChunkingConfig
    retrieval: RetrievalConfig
    llm_params: LLMParamsConfig


class ConfigUpdateRequest(BaseModel):
    chunking: ChunkingConfig
    retrieval: RetrievalConfig
    llm_params: LLMParamsConfig
    qdrant: Optional[QdrantConfig] = None
    models: Optional[ModelsConfig] = None

    @model_validator(mode="after")
    def validate_top_k_raw(self):
        if self.retrieval.top_k_raw < self.retrieval.top_k:
            raise ValueError("Số kết quả thô (top_k_raw) phải lớn hơn hoặc bằng top_k")
        return self


class DocumentItemResponse(BaseModel):
    filename: str
    size_bytes: int
    size_readable: str
    updated_at: str


class IngestStatusResponse(BaseModel):
    status: str  # "idle", "running", "completed", "failed"
    message: str
    elapsed_seconds: Optional[float] = None
    total_chunks: Optional[int] = None


class AdminUserResponse(BaseModel):
    user_id: int
    username: str
    role: str
    created_at: datetime
    session_count: int = 0

    class Config:
        from_attributes = True


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|user)$")


class SystemStatsResponse(BaseModel):
    total_users: int
    total_sessions: int
    total_messages: int
    zero_citation_count: int


class LowConfidenceQueryResponse(BaseModel):
    message_id: int
    session_id: str
    username: Optional[str] = None
    user_question: str
    ai_answer: str
    created_at: datetime

