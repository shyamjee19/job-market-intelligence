from openai import AzureOpenAI

from ai.providers.base import ChatMessage, ChatProvider, ChatResult, EmbeddingProvider
from config.settings import settings
from utils.exceptions import APIRequestError

_EMBEDDING_DIMENSIONS = 1536  # matches OpenAI's text-embedding-3-small; adjust if your deployment differs


def _client() -> AzureOpenAI:
    if not (settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT):
        raise APIRequestError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must both be set")
    return AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )


class AzureOpenAIChatProvider(ChatProvider):
    """Azure OpenAI addresses models by *deployment name*, not model name -
    AZURE_OPENAI_CHAT_DEPLOYMENT must match whatever you named the
    deployment in Azure AI Studio, not e.g. "gpt-4o" itself."""

    name = "azure_openai"

    def __init__(self):
        if not settings.AZURE_OPENAI_CHAT_DEPLOYMENT:
            raise APIRequestError("AZURE_OPENAI_CHAT_DEPLOYMENT is not set")
        self._client = _client()
        self._deployment = settings.AZURE_OPENAI_CHAT_DEPLOYMENT

    def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> ChatResult:
        response = self._client.chat.completions.create(
            model=self._deployment,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
        )
        choice = response.choices[0].message.content or ""
        usage = response.usage
        return ChatResult(
            text=choice,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
        )


class AzureOpenAIEmbeddingProvider(EmbeddingProvider):
    name = "azure_openai"
    dimensions = _EMBEDDING_DIMENSIONS

    def __init__(self):
        if not settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
            raise APIRequestError("AZURE_OPENAI_EMBEDDING_DEPLOYMENT is not set")
        self._client = _client()
        self._deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self._deployment, input=texts)
        return [item.embedding for item in response.data]
