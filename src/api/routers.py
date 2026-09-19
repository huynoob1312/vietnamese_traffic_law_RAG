import os
from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_rag_components
from src.api.schemas import ChatRequest, ChatResponse
from src.ingestion.docx_loader import load_and_chunk_data
from src.vectordb.qdrant_client import push_to_qdrant

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, components: dict = Depends(get_rag_components)):
    process_func = components.get("process")
    qa_chain = components.get("chain")

    if not process_func or not qa_chain:
        raise HTTPException(status_code=503, detail="RAG legal is not ready")

    try:
        processed = process_func(
            {
                "input": request.question
            }
        )

        answer = qa_chain.invoke(processed)
        return ChatResponse(answer=answer)

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
