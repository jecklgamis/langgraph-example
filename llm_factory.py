import os

from langchain_anthropic import ChatAnthropic
from langchain_cohere import ChatCohere
from langchain_fireworks import ChatFireworks
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter
from langchain_together import ChatTogether

_DEFAULT_MODELS = {
    "ollama": "llama3.2",
    "openai": "gpt-4.1-nano",
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-sonnet-4-6",
    "groq": "llama-3.3-70b-versatile",
    "mistral": "mistral-large-latest",
    "openrouter": "openrouter/auto",
    "cohere": "command-r-plus",
    "together": "meta-llama/Llama-3.3-70b-instruct-turbo",
    "fireworks": "accounts/fireworks/models/llama-v3p3-70b-instruct",
    "deepseek": "deepseek-chat",
    "xai": "grok-3-mini",
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
    "anthropic": (
        ChatAnthropic,
        {
            "api_key": os.environ.get("ANTHROPIC_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "groq": (
        ChatGroq,
        {
            "api_key": os.environ.get("GROQ_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "mistral": (
        ChatMistralAI,
        {
            "api_key": os.environ.get("MISTRAL_API_KEY"),
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
    "cohere": (
        ChatCohere,
        {
            "cohere_api_key": os.environ.get("COHERE_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "together": (
        ChatTogether,
        {
            "together_api_key": os.environ.get("TOGETHER_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "fireworks": (
        ChatFireworks,
        {
            "fireworks_api_key": os.environ.get("FIREWORKS_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "deepseek": (
        ChatOpenAI,
        {
            "base_url": "https://api.deepseek.com/v1",
            "api_key": os.environ.get("DEEPSEEK_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "xai": (
        ChatOpenAI,
        {
            "base_url": "https://api.x.ai/v1",
            "api_key": os.environ.get("XAI_API_KEY"),
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
