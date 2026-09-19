from langchain_ollama.llms import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.config import LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE
import os

def get_llm():
    if LLM_PROVIDER.lower() == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Vui lòng cấu hình GEMINI_API_KEY")

        return ChatGoogleGenerativeAI(
            model=LLM_MODEL, 
            google_api_key=api_key,
            timeout=120.0,
            max_retries=3
        )
    else:
        return OllamaLLM(
            model=LLM_MODEL, 
            temperature=LLM_TEMPERATURE,
            timeout=300.0
        )
