from langchain_ollama.llms import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
import src.utils.config as cfg
import os

def get_llm():
    if cfg.LLM_PROVIDER.lower() == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Vui lòng cấu hình GEMINI_API_KEY")

        return ChatGoogleGenerativeAI(
            model=cfg.LLM_MODEL, 
            google_api_key=api_key,
            timeout=120.0,
            max_retries=3
        )
    else:
        return OllamaLLM(
            model=cfg.LLM_MODEL, 
            temperature=cfg.LLM_TEMPERATURE,
            timeout=300.0
        )
