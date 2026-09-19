import socket
import urllib3
import warnings
from dotenv import load_dotenv
from src.retrieval.rag_chain import build_rag_chain
from src.api.dependencies import rag_components
from src.api.routers import router as api_router

from fastapi import FastAPI
from contextlib import  asynccontextmanager
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
    # load model
    process_func, qa_chain = build_rag_chain()

    #nap vao ram
    rag_components["process"] = process_func
    rag_components["chain"] = qa_chain
    yield

    rag_components.clear()

app = FastAPI(title= "LEGAL RAG", lifespan=lifespan)
app.include_router(api_router, prefix="/api")

if __name__ == '__main__':
    uvicorn.run("main:app", port=8000, reload=True)