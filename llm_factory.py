import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter

_DEFAULT_MODELS = {
    "ollama": "llama3.2",
    "ollama_native": "llama3.2",
    "openai": "gpt-4.1-nano",
    "gemini": "gemini-2.5-flash",
    "openrouter": "openrouter/free",
}

_PROVIDERS = {
    "ollama": (
        ChatOpenAI,
        {
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "ollama_native": (
        ChatOllama,
        {
            "base_url": "http://localhost:11434",
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "openai": (
        ChatOpenAI,
        {
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "gemini": (
        ChatGoogleGenerativeAI,
        {
            "api_key": os.environ.get("GEMINI_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "openrouter": (
        ChatOpenRouter,
        {
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
}


def create_llm(provider: str = None):
    provider = provider or os.environ.get("LLM_PROVIDER", "ollama")
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    model = os.environ.get("LLM_MODEL") or _DEFAULT_MODELS[provider]
    cls, kwargs = _PROVIDERS[provider]
    return cls(model=model, **kwargs)
