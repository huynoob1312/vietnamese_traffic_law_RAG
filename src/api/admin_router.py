import os
import shutil
import time
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db.database import get_db
from src.db.models import User, ChatSession, ChatMessage
from src.api.dependencies import get_admin_user, rag_components
from src.api.schemas import (
    AppConfigResponse,
    ConfigUpdateRequest,
    DocumentItemResponse,
    IngestStatusResponse,
    AdminUserResponse,
    UserRoleUpdateRequest,
    SystemStatsResponse,
    LowConfidenceQueryResponse,
)
from src.utils.config import reload_config
from src.retrieval.rag_chain import build_rag_chain
from src.ingestion.docx_loader import load_and_chunk_data
from src.vectordb.qdrant_client import push_to_qdrant

router = APIRouter(prefix="/admin", tags=["Admin Management"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Global Ingestion Background Task State
ingest_state: Dict[str, Any] = {
    "status": "idle",  # "idle", "running", "completed", "failed"
    "message": "Hệ thống sẵn sàng",
    "start_time": None,
    "elapsed_seconds": None,
    "total_chunks": None,
}


# ==========================================
# 1. Config Management (Task 11)
# ==========================================

@router.get("/config", response_model=AppConfigResponse)
def get_system_config(admin: User = Depends(get_admin_user)):
    """Đọc và trả về cấu hình hiện hành từ config.yaml."""
    if not os.path.exists(CONFIG_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tệp config.yaml trên máy chủ"
        )
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg_data = yaml.safe_load(f)
        return cfg_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi đọc file cấu hình: {str(e)}"
        )


@router.put("/config")
def update_system_config(
    request: ConfigUpdateRequest,
    admin: User = Depends(get_admin_user)
):
    """
    Xác thực và ghi đè cấu hình mới vào config.yaml (Use Case 3.2.3.8).
    Tự động hot-reload RAG chain trong bộ nhớ cho các tham số runtime.
    """
    if not os.path.exists(CONFIG_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tệp config.yaml trên máy chủ"
        )

    # 1. Đọc config hiện tại để bảo toàn các trường tùy chọn nếu request không gửi
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            current_cfg = yaml.safe_load(f) or {}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi đọc file config gốc: {str(e)}"
        )

    # 2. Tạo bản sao lưu dự phòng config.yaml.bak
    bak_path = CONFIG_PATH + ".bak"
    try:
        shutil.copyfile(CONFIG_PATH, bak_path)
    except Exception as e:
        print(f"⚠️ Không thể tạo bản sao lưu config: {e}")

    # 3. Cập nhật các khối dữ liệu
    current_cfg["chunking"] = {
        "thresh_dieu": request.chunking.thresh_dieu,
        "thresh_khoan_default": request.chunking.thresh_khoan_default,
        "min_chunk": request.chunking.min_chunk,
        "min_chunk_diem": request.chunking.min_chunk_diem,
    }

    current_cfg["retrieval"] = {
        "search_type": request.retrieval.search_type,
        "top_k": request.retrieval.top_k,
        "use_reranker": request.retrieval.use_reranker,
        "reranker_model": request.retrieval.reranker_model,
        "top_k_raw": request.retrieval.top_k_raw,
    }

    llm_dict = {
        "provider": request.llm_params.provider,
        "model": request.llm_params.model,
    }
    if request.llm_params.temperature is not None:
        llm_dict["temperature"] = request.llm_params.temperature
    current_cfg["llm_params"] = llm_dict

    if request.qdrant:
        current_cfg["qdrant"] = {"collection_name": request.qdrant.collection_name}
    if request.models:
        current_cfg["models"] = {
            "embedding": request.models.embedding,
            "llm": request.models.llm,
        }

    # 4. Ghi đè an toàn vào config.yaml
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(current_cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi ghi đè config.yaml: {str(e)}"
        )

    # 5. Hot-reload config và RAG Chain trong bộ nhớ
    try:
        reload_config()
        process_func, qa_chain = build_rag_chain()
        rag_components["process"] = process_func
        rag_components["chain"] = qa_chain
        hot_reload_msg = "và đã hot-reload RAG pipeline thành công"
    except Exception as e:
        hot_reload_msg = f"nhưng hot-reload RAG pipeline gặp lỗi: {str(e)}"

    return {
        "status": "success",
        "message": f"Cập nhật cấu hình thành công {hot_reload_msg}.",
        "config": current_cfg,
    }


# ==========================================
# 2. Knowledge & Ingestion Management (Task 12)
# ==========================================

def _format_size(size_bytes: int) -> str:
    """Chuyển đổi byte sang định dạng dễ đọc (KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


@router.get("/documents", response_model=List[DocumentItemResponse])
def list_documents(admin: User = Depends(get_admin_user)):
    """Liệt kê danh sách các văn bản luật trong thư mục data/."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

    items = []
    allowed_exts = {".docx", ".pdf", ".txt"}
    try:
        for fname in os.listdir(DATA_DIR):
            ext = os.path.splitext(fname)[1].lower()
            if ext in allowed_exts:
                fpath = os.path.join(DATA_DIR, fname)
                st = os.stat(fpath)
                mtime_str = datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y %H:%M")
                items.append(
                    DocumentItemResponse(
                        filename=fname,
                        size_bytes=st.st_size,
                        size_readable=_format_size(st.st_size),
                        updated_at=mtime_str,
                    )
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể đọc thư mục tài liệu: {str(e)}")

    return items


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    admin: User = Depends(get_admin_user)
):
    """Tải lên văn bản quy phạm pháp luật mới (.docx, .pdf) vào thư mục data/."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".docx", ".pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hệ thống chỉ hỗ trợ định dạng tệp .docx hoặc .pdf"
        )

    os.makedirs(DATA_DIR, exist_ok=True)
    target_path = os.path.join(DATA_DIR, file.filename)

    try:
        contents = await file.read()
        if len(contents) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kích thước tệp vượt quá giới hạn tối đa 25MB"
            )

        with open(target_path, "wb") as f:
            f.write(contents)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu tệp tải lên: {str(e)}")

    return {
        "status": "success",
        "message": f"Đã tải lên tệp '{file.filename}' thành công",
        "filename": file.filename,
        "size_readable": _format_size(len(contents)),
    }


@router.delete("/documents/{filename}")
def delete_document(
    filename: str,
    admin: User = Depends(get_admin_user)
):
    """Xóa văn bản luật khỏi thư mục data/."""
    safe_filename = os.path.basename(filename)
    target_path = os.path.join(DATA_DIR, safe_filename)

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tệp '{safe_filename}' trong thư mục dữ liệu"
        )

    try:
        os.remove(target_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa tệp: {str(e)}")

    return {
        "status": "success",
        "message": f"Đã xóa tệp '{safe_filename}' thành công",
    }


def _run_background_ingest():
    """Tác vụ ngầm thực thi chunking và đánh vector Qdrant."""
    global ingest_state
    start_t = time.time()
    try:
        # Xóa file cache cũ để buộc load lại từ data/
        cache_path = os.path.join(DATA_DIR, "cached_chunks.pkl")
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except Exception:
                pass

        chunks = load_and_chunk_data(DATA_DIR)
        if not chunks:
            ingest_state["status"] = "failed"
            ingest_state["message"] = "Không tìm thấy dữ liệu hợp lệ trong thư mục data"
            ingest_state["elapsed_seconds"] = round(time.time() - start_t, 1)
            return

        push_to_qdrant(chunks)

        # Cập nhật RAG chain sau khi nạp xong
        try:
            process_func, qa_chain = build_rag_chain()
            rag_components["process"] = process_func
            rag_components["chain"] = qa_chain
        except Exception:
            pass

        ingest_state["status"] = "completed"
        ingest_state["total_chunks"] = len(chunks)
        ingest_state["elapsed_seconds"] = round(time.time() - start_t, 1)
        ingest_state["message"] = f"Nạp thành công {len(chunks)} chunks vào cơ sở dữ liệu Vector Qdrant"
    except Exception as e:
        ingest_state["status"] = "failed"
        ingest_state["message"] = f"Lỗi trong quá trình Ingestion: {str(e)}"
        ingest_state["elapsed_seconds"] = round(time.time() - start_t, 1)


@router.post("/ingest")
def trigger_ingest(
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_admin_user)
):
    """Kích hoạt tiến trình nạp tri thức và Re-index Qdrant dưới nền."""
    global ingest_state
    if ingest_state["status"] == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tiến trình Ingestion đang được thực thi, vui lòng đợi hoàn tất"
        )

    ingest_state["status"] = "running"
    ingest_state["message"] = "Đang xử lý phân mảnh (chunking) và đẩy vector vào Qdrant..."
    ingest_state["start_time"] = time.time()
    ingest_state["elapsed_seconds"] = 0
    ingest_state["total_chunks"] = None

    background_tasks.add_task(_run_background_ingest)

    return {
        "status": "accepted",
        "message": "Đã tiếp nhận yêu cầu Re-index dữ liệu. Quá trình đang chạy ngầm."
    }


@router.get("/ingest/status", response_model=IngestStatusResponse)
def get_ingest_status(admin: User = Depends(get_admin_user)):
    """Kiểm tra trạng thái tiến trình Ingestion hiện tại."""
    global ingest_state
    elapsed = ingest_state["elapsed_seconds"]
    if ingest_state["status"] == "running" and ingest_state["start_time"]:
        elapsed = round(time.time() - ingest_state["start_time"], 1)

    return IngestStatusResponse(
        status=ingest_state["status"],
        message=ingest_state["message"],
        elapsed_seconds=elapsed,
        total_chunks=ingest_state["total_chunks"],
    )


# ==========================================
# 3. Users & Analytics Management (Task 13)
# ==========================================

@router.get("/users", response_model=List[AdminUserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Lấy danh sách người dùng kèm số lượng phiên tra cứu đã tạo."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    results = []
    for u in users:
        session_cnt = len(u.sessions) if u.sessions else 0
        results.append(
            AdminUserResponse(
                user_id=u.user_id,
                username=u.username,
                role=u.role,
                created_at=u.created_at,
                session_count=session_cnt,
            )
        )
    return results


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    request: UserRoleUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Cập nhật vai trò người dùng (admin <-> user)."""
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng được chỉ định"
        )

    # Chặn admin tự hạ quyền của chính mình
    if target_user.user_id == admin.user_id and request.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể tự hạ quyền quản trị viên của chính mình"
        )

    target_user.role = request.role
    db.commit()
    db.refresh(target_user)

    return {
        "status": "success",
        "message": f"Đã cập nhật vai trò của tài khoản '{target_user.username}' thành '{target_user.role}'",
        "user_id": target_user.user_id,
        "role": target_user.role,
    }


@router.get("/stats", response_model=SystemStatsResponse)
def get_system_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Thống kê tổng quan số liệu người dùng và lịch sử tra cứu của hệ thống."""
    total_users = db.query(func.count(User.user_id)).scalar() or 0
    total_sessions = db.query(func.count(ChatSession.session_id)).scalar() or 0
    total_messages = db.query(func.count(ChatMessage.message_id)).scalar() or 0

    # Lấy các tin nhắn AI có citations rỗng hoặc None
    zero_citation_count = (
        db.query(func.count(ChatMessage.message_id))
        .filter(ChatMessage.role == "ai")
        .filter((ChatMessage.citations == None) | (ChatMessage.citations == []) | (ChatMessage.citations == "[]"))
        .scalar() or 0
    )

    return SystemStatsResponse(
        total_users=total_users,
        total_sessions=total_sessions,
        total_messages=total_messages,
        zero_citation_count=zero_citation_count,
    )


@router.get("/audit/low-confidence", response_model=List[LowConfidenceQueryResponse])
def get_low_confidence_queries(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Trích xuất các câu hỏi của người dùng mà AI không tìm thấy nguồn luật tham chiếu
    (hoặc citations rỗng) để Admin phát hiện lỗ hổng tri thức pháp lý cần bổ sung.
    """
    ai_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.role == "ai")
        .filter((ChatMessage.citations == None) | (ChatMessage.citations == []) | (ChatMessage.citations == "[]"))
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
        .all()
    )

    results = []
    for ai_msg in ai_messages:
        # Tìm tin nhắn user ngay trước tin nhắn AI này trong cùng session
        user_msg = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == ai_msg.session_id)
            .filter(ChatMessage.role == "user")
            .filter(ChatMessage.created_at <= ai_msg.created_at)
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        
        # Tìm session để lấy username
        sess = db.query(ChatSession).filter(ChatSession.session_id == ai_msg.session_id).first()
        uname = sess.user.username if sess and sess.user else "Guest"

        results.append(
            LowConfidenceQueryResponse(
                message_id=ai_msg.message_id,
                session_id=ai_msg.session_id,
                username=uname,
                user_question=user_msg.content if user_msg else "(Câu hỏi không xác định)",
                ai_answer=ai_msg.content[:250] + ("..." if len(ai_msg.content) > 250 else ""),
                created_at=ai_msg.created_at,
            )
        )

    return results
