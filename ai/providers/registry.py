"""Selects the active chat/embedding provider from config/settings.py.
Providers are constructed lazily (only the one actually selected touches
its SDK/credentials), so an unconfigured provider you're not using never
raises just by being imported."""
from ai.providers.base import ChatProvider, EmbeddingProvider
from config.settings import settings


def get_chat_provider() -> ChatProvider:
    provider = settings.AI_CHAT_PROVIDER

    if provider == "openai":
        from ai.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()
    if provider == "claude":
        from ai.providers.claude_provider import ClaudeProvider
        return ClaudeProvider()
    if provider == "azure_openai":
        from ai.providers.azure_openai_provider import AzureOpenAIChatProvider
        return AzureOpenAIChatProvider()
    if provider == "ollama":
        from ai.providers.ollama_provider import OllamaProvider
        return OllamaProvider()

    raise ValueError(f"Unknown AI_CHAT_PROVIDER '{provider}'. Expected one of: openai, claude, azure_openai, ollama")


def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.AI_EMBEDDING_PROVIDER

    if provider == "openai":
        from ai.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()
    if provider == "azure_openai":
        from ai.providers.azure_openai_provider import AzureOpenAIEmbeddingProvider
        return AzureOpenAIEmbeddingProvider()
    if provider == "ollama":
        from ai.providers.ollama_provider import OllamaProvider
        return OllamaProvider()
    if provider == "claude":
        from ai.providers.claude_provider import ClaudeEmbeddingUnavailable
        return ClaudeEmbeddingUnavailable()

    raise ValueError(f"Unknown AI_EMBEDDING_PROVIDER '{provider}'. Expected one of: openai, azure_openai, ollama")
