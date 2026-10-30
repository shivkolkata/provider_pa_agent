import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()
    #OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    #GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    #GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Model defaults
    DEFAULT_OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    DEFAULT_GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    DEFAULT_GROK_MODEL: str = os.getenv("GEMINI_MODEL", "qwen/qwen3.8-27b")