import os
from langchain_openai import ChatOpenAI
#from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from provider_pa_agent.config import Config

def get_llm(temperature: float = 0.0, model_name: str = None): # type: ignore
    """
    Centralized LLM gateway factory. 
    Reads LLM_PROVIDER from config/environment to instantiate the target vendor model.
    """
    provider = Config.LLM_PROVIDER
    
    if provider == "openai":
       # if not Config.OPENAI_API_KEY:
        #    raise ValueError("OPENAI_API_KEY is missing in environment variables.")
        return ChatOpenAI(
            model=model_name or Config.DEFAULT_OPENAI_MODEL,
            temperature=temperature,
            #api_key=Config.OPENAI_API_KEY
        )
    #elif provider == "gemini":
        #if not Config.GEMINI_API_KEY:
        #    raise ValueError("GEMINI_API_KEY is missing in environment variables.")
    #    return ChatGoogleGenerativeAI(
    #        model=model_name or Config.DEFAULT_GEMINI_MODEL,
    #        temperature=temperature,
    #        #google_api_key=Config.GEMINI_API_KEY
    #    )
    elif provider == "grok":
        #if not Config.GEMINI_API_KEY:
        #    raise ValueError("GEMINI_API_KEY is missing in environment variables.")
        return ChatGroq(
            model=model_name or Config.DEFAULT_GROK_MODEL,
            temperature=temperature,
        #    google_api_key=Config.GEMINI_API_KEY
        )
    else:
        raise ValueError(f"Unsupported LLM provider: '{provider}'. Choose 'openai' or 'gemini' or 'grok'. ")