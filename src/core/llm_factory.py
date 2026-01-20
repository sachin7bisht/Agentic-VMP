# ==========================================
# File: src/core/llm_factory.py
# ==========================================
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import settings

class LLMFactory:
    """
    Factory class to instantiate LLM models based on configuration.
    Decouples application logic from specific model providers.
    """

    @staticmethod
    def get_llm(temperature: float = 0.0, max_tokens: Optional[int] = None) -> BaseChatModel:
        """
        Returns a configured Chat Model instance.
        
        Args:
            temperature (float): Creativity control (0.0 = deterministic, 1.0 = creative).
            max_tokens (int, optional): Limit response length.
            
        Returns:
            BaseChatModel: A LangChain compatible chat model.
        """
        provider = settings.LLM_PROVIDER
        
        if provider == "openai":
            return LLMFactory._create_openai_model(temperature, max_tokens)
        elif provider == "gemini":
            return LLMFactory._create_gemini_model(temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported LLM Provider: {provider}")

    @staticmethod
    def _create_openai_model(temperature: float, max_tokens: Optional[int]) -> ChatOpenAI:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API Key is missing in settings.")
            
        return ChatOpenAI(
            model=settings.OPENAI_MODEL_NAME,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.OPENAI_API_KEY
        )

    @staticmethod
    def _create_gemini_model(temperature: float, max_tokens: Optional[int]) -> ChatGoogleGenerativeAI:
        if not settings.GOOGLE_API_KEY:
            raise ValueError("Google API Key is missing in settings.")
            
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL_NAME,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=settings.GOOGLE_API_KEY,
            convert_system_message_to_human=True # Helper for Gemini compatibility
        )

# Simple usage example for testing
if __name__ == "__main__":
    try:
        llm = LLMFactory.get_llm()
        print(f"Successfully loaded: {type(llm).__name__}")
    except Exception as e:
        print(f"Failed to load LLM: {e}")