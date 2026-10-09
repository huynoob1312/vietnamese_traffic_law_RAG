import socket
import urllib3
import warnings
from dotenv import load_dotenv
from src.retrieval.rag_chain import build_rag_chain
from src.api.dependencies import rag_components
from src.api.routers import router as api_router
from src.api.auth_router import router as auth_router
from src.api.history_router import router as history_router
from src.api.admin_router import router as admin_router
from src.db.init_db import init_tables

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

warnings.filterwarnings("ignore")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

import sys
class CleanStderr:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
    def write(self, s):
        if "Direct use of automatic function calling (AFC)" not in s and "Models.generate_content" not in s and "Chat.send_message" not in s:
            self.original_stderr.write(s)
    def flush(self):
        self.original_stderr.flush()
sys.stderr = CleanStderr(sys.stderr)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo CSDL MySQL
    try:
        init_tables()
    except Exception as e:
        print(f"⚠️ Lỗi khởi tạo MySQL: {e}")

    # load model
    try:
        process_func, qa_chain = build_rag_chain()
        rag_components["process"] = process_func
        rag_components["chain"] = qa_chain
        print("✅ Đã khởi tạo thành công RAG Chain!")
    except Exception as e:
        print(e)
    yield

    rag_components.clear()

app = FastAPI(title="LEGAL RAG", lifespan=lifespan)

# CORS middleware for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# Mount React frontend static assets if built
DIST_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

if __name__ == '__main__':
    uvicorn.run("main:app", port=8000, reload=True)