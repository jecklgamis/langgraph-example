import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter


def get_default_provider():
    return os.environ.get("LLM_PROVIDER", "ollama")


LLM_CONFIGS = {
    # Ollama in OpenAI-compatible API mode (default path, no langchain_ollama dependency required)
    "ollama": {
        "provider": "openai",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    },
    # Ollama native mode (requires langchain-ollama package)
    "ollama_native": {
        "provider": "ollama_native",
        "model": "llama3.2",
        "base_url": "http://localhost:11434",
        "api_key": "ollama",
    },
    "openai": {
        "provider": "openai",
        "model": "gpt-4.1-nano",
        "api_key": os.environ.get("OPENAI_API_KEY"),
    },
    "gemini": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "api_key": os.environ.get("GEMINI_API_KEY"),
    },
    "openrouter": {
        "provider": "openrouter",
        "model": "openrouter/free",
        "api_key": os.environ.get("OPENROUTER_API_KEY"),
    },
}


def create_llm(provider: str = None) -> any:
    config = {**LLM_CONFIGS[provider or get_default_provider()]}
    provider_type = config.pop("provider")

    if provider_type == "openai":
        return ChatOpenAI(**config)
    elif provider_type == "google_genai":
        return ChatGoogleGenerativeAI(**config)
    elif provider_type == "ollama_native":
        return ChatOllama(**config)
    elif provider_type == "openrouter":
        return ChatOpenRouter(**config)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
