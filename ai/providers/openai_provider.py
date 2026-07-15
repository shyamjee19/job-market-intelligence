from openai import OpenAI

from ai.providers.base import ChatMessage, ChatProvider, ChatResult, EmbeddingProvider
from config.settings import settings
from utils.exceptions import APIRequestError

# text-embedding-3-small's native output size - see
# https://platform.openai.com/docs/guides/embeddings
_EMBEDDING_DIMENSIONS = 1536


class OpenAIProvider(ChatProvider, EmbeddingProvider):
    name = "openai"
    dimensions = _EMBEDDING_DIMENSIONS

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise APIRequestError("OPENAI_API_KEY is not set")
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._chat_model = settings.OPENAI_CHAT_MODEL
        self._embedding_model = settings.OPENAI_EMBEDDING_MODEL

    def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> ChatResult:
        response = self._client.chat.completions.create(
            model=self._chat_model,
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

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self._embedding_model, input=texts)
        return [item.embedding for item in response.data]
