import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter

_PROVIDERS = {
    "ollama": (
        ChatOpenAI,
        {
            "model": "llama3.2",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
        },
    ),
    "ollama_native": (
        ChatOllama,
        {
            "model": "llama3.2",
            "base_url": "http://localhost:11434",
        },
    ),
    "openai": (
        ChatOpenAI,
        {
            "model": "gpt-4.1-nano",
            "api_key": os.environ.get("OPENAI_API_KEY"),
        },
    ),
    "gemini": (
        ChatGoogleGenerativeAI,
        {
            "model": "gemini-2.5-flash",
            "api_key": os.environ.get("GEMINI_API_KEY"),
        },
    ),
    "openrouter": (
        ChatOpenRouter,
        {
            "model": "openrouter/free",
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
        },
    ),
}

_DEFAULTS = {"temperature": 0.7, "max_tokens": 4096}


def create_llm(provider: str = None):
    provider = provider or os.environ.get("LLM_PROVIDER", "ollama")
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    print(f"Using {provider} LLM provider")
    cls, kwargs = _PROVIDERS[provider]
    return cls(**_DEFAULTS, **kwargs)
