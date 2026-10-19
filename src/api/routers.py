import os
import re
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.api.dependencies import get_rag_components, get_optional_current_user
from src.api.schemas import ChatRequest, ChatResponse
from src.db.database import get_db, SessionLocal
from src.db.models import User, ChatSession, ChatMessage
from src.ingestion.docx_loader import load_and_chunk_data
from src.vectordb.qdrant_client import push_to_qdrant

router = APIRouter()

def filter_citations_by_answer(citations: list[dict], answer: str) -> list[dict]:
    """
    Lọc danh sách citations để chỉ giữ lại đúng các Điều/Khoản mà AI thực sự trích dẫn trong câu trả lời.
    """
    if not citations or not answer:
        return citations

    # 1. Tìm tất cả các trích dẫn dạng (Nguồn: ...) do AI sinh ra
    cite_matches = re.findall(r'Nguồn:\s*([^\)\*\n\r]+)', answer, re.IGNORECASE)

    if not cite_matches:
        # Nếu AI không sinh định dạng (Nguồn: ...), tìm các Điều luật được nhắc đến trong bài
        dieu_matches = set(re.findall(r'Điều\s*(\d+)', answer, re.IGNORECASE))
        if dieu_matches:
            matched = [c for c in citations if str(c.get("dieu", "")).strip() in dieu_matches]
            if matched:
                return matched[:5]
        return citations[:5]

    target_specs = []
    for c_text in cite_matches:
        dieu = re.search(r'Điều\s*(\d+)', c_text, re.IGNORECASE)
        khoan = re.search(r'Khoản\s*(\d+)', c_text, re.IGNORECASE)
        diem = re.search(r'Điểm\s*([a-zđA-ZĐ])', c_text, re.IGNORECASE)
        target_specs.append({
            "dieu": dieu.group(1) if dieu else None,
            "khoan": khoan.group(1) if khoan else None,
            "diem": diem.group(1).lower() if diem else None,
        })

    matched = []
    seen = set()

    for spec in target_specs:
        spec_dieu = spec["dieu"]
        spec_khoan = spec["khoan"]
        spec_diem = spec["diem"]

        best_match = None
        for c in citations:
            c_dieu = str(c.get("dieu", "")).strip()
            c_khoan = str(c.get("khoan", "")).strip()
            c_diem = str(c.get("diem", "")).strip().lower()

            if spec_dieu and c_dieu == spec_dieu:
                if spec_khoan and spec_diem and c_khoan == spec_khoan and c_diem == spec_diem:
                    best_match = c
                    break
                elif spec_khoan and c_khoan == spec_khoan and not best_match:
                    best_match = c
                elif not best_match and not spec_khoan:
                    best_match = c

        if best_match:
            key = (best_match.get("source"), best_match.get("dieu"), best_match.get("khoan"), best_match.get("diem"))
            if key not in seen:
                seen.add(key)
                matched.append(best_match)

    # Nếu vẫn chưa tìm thấy chính xác, fallback tìm theo Điều
    if not matched:
        for spec in target_specs:
            if spec["dieu"]:
                for c in citations:
                    if str(c.get("dieu", "")).strip() == spec["dieu"]:
                        key = (c.get("source"), c.get("dieu"), c.get("khoan"), c.get("diem"))
                        if key not in seen:
                            seen.add(key)
                            matched.append(c)
                        if len(matched) >= 5:
                            break

    return matched if matched else citations[:5]


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    components: dict = Depends(get_rag_components),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    process_func = components.get("process")
    qa_chain = components.get("chain")

    if not process_func or not qa_chain:
        raise HTTPException(status_code=503, detail="RAG legal is not ready")

    try:
        prompt_text = request.prompt
        processed = process_func({"input": prompt_text})
        citations = processed.get("citations", [])

        # Tạo input cho qa_chain
        chain_input = {
            "context": processed.get("context", ""),
            "input": processed.get("input", prompt_text)
        }
        answer = qa_chain.invoke(chain_input)
        citations = filter_citations_by_answer(citations, answer)

        session_id = request.session_id

        # Nếu user đã đăng nhập, tự động lưu lịch sử
        if current_user:
            if not session_id:
                session_id = str(uuid.uuid4())
                title = prompt_text.strip()[:40] + ("..." if len(prompt_text) > 40 else "")
                new_session = ChatSession(
                    session_id=session_id,
                    user_id=current_user.user_id,
                    title=title
                )
                db.add(new_session)
                db.commit()
            else:
                existing_session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id,
                    ChatSession.user_id == current_user.user_id
                ).first()
                if not existing_session:
                    session_id = str(uuid.uuid4())
                    title = request.question.strip()[:40] + ("..." if len(request.question) > 40 else "")
                    new_session = ChatSession(
                        session_id=session_id,
                        user_id=current_user.user_id,
                        title=title
                    )
                    db.add(new_session)
                    db.commit()

            # Lưu user message
            user_msg = ChatMessage(
                session_id=session_id,
                role="user",
                content=request.question
            )
            # Lưu AI message
            ai_msg = ChatMessage(
                session_id=session_id,
                role="ai",
                content=answer,
                citations=citations
            )
            db.add(user_msg)
            db.add(ai_msg)

            # Cập nhật updated_at cho session
            session_obj = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if session_obj:
                session_obj.updated_at = func.now()

            db.commit()

        return ChatResponse(
            answer=answer,
            citations=citations,
            session_id=session_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream", tags=["Chat"])
async def chat_stream(
    request: ChatRequest,
    components: dict = Depends(get_rag_components),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    process_func = components.get("process")
    qa_chain = components.get("chain")

    if not process_func or not qa_chain:
        raise HTTPException(status_code=503, detail="RAG legal is not ready")

    try:
        prompt_text = request.prompt
        processed = process_func({"input": prompt_text})
        citations = processed.get("citations", [])
        chain_input = {
            "context": processed.get("context", ""),
            "input": processed.get("input", prompt_text)
        }

        # Xử lý session_id cho user đã đăng nhập
        session_id = request.session_id
        user_id = current_user.user_id if current_user else None

        if current_user:
            if not session_id:
                session_id = str(uuid.uuid4())
                title = prompt_text.strip()[:40] + ("..." if len(prompt_text) > 40 else "")
                new_session = ChatSession(
                    session_id=session_id,
                    user_id=current_user.user_id,
                    title=title
                )
                db.add(new_session)
                db.commit()
            else:
                existing_session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id,
                    ChatSession.user_id == current_user.user_id
                ).first()
                if not existing_session:
                    session_id = str(uuid.uuid4())
                    title = prompt_text.strip()[:40] + ("..." if len(prompt_text) > 40 else "")
                    new_session = ChatSession(
                        session_id=session_id,
                        user_id=current_user.user_id,
                        title=title
                    )
                    db.add(new_session)
                    db.commit()

            # Lưu ngay tin nhắn user
            user_msg = ChatMessage(
                session_id=session_id,
                role="user",
                content=prompt_text
            )
            db.add(user_msg)
            db.commit()

        def sse_event_generator():
            # 1. Phát event session nếu có
            if session_id:
                yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"

            # 2. Phát luồng token
            full_ai_content = []
            try:
                for chunk in qa_chain.stream(chain_input):
                    full_ai_content.append(chunk)
                    yield f"event: delta\ndata: {json.dumps({'content': chunk, 'text': chunk})}\n\n"
            except Exception as stream_err:
                err_msg = f"\n\n⚠️ Lỗi kết nối mô hình LLM: {str(stream_err)}. Vui lòng kiểm tra lại GEMINI_API_KEY hoặc cấu hình Ollama."
                full_ai_content.append(err_msg)
                yield f"event: delta\ndata: {json.dumps({'content': err_msg, 'text': err_msg})}\n\n"

            full_answer = "".join(full_ai_content)
            final_citations = filter_citations_by_answer(citations, full_answer)

            # 3. Phát event citations
            yield f"event: citations\ndata: {json.dumps({'citations': final_citations}, ensure_ascii=False)}\n\n"

            # 4. Lưu câu trả lời AI vào DB nếu user đăng nhập
            if user_id and session_id:
                save_db = SessionLocal()
                try:
                    ai_msg = ChatMessage(
                        session_id=session_id,
                        role="ai",
                        content=full_answer,
                        citations=final_citations
                    )
                    save_db.add(ai_msg)
                    sess = save_db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
                    if sess:
                        sess.updated_at = func.now()
                    save_db.commit()
                except Exception as ex:
                    print(f"Lỗi lưu lịch sử chat: {ex}")
                finally:
                    save_db.close()

            # 5. Phát event done
            yield f"event: done\ndata: {json.dumps({'status': 'completed', 'session_id': session_id})}\n\n"

        return StreamingResponse(
            sse_event_generator(),
            media_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", tags=["Data Management"])
async def ingest():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    base_data_dir = os.path.join(base_dir, "data")

    chunks = load_and_chunk_data(base_data_dir)

    if not chunks:
        raise HTTPException(status_code=404, detail="not found folder data")

    try:
        push_to_qdrant(chunks)
        return {
            "status": "success",
            "message": f"{len(chunks)} chunk was uploaded to qdrant"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
