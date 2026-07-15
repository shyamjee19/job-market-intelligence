import requests

from ai.providers.base import ChatMessage, ChatProvider, ChatResult, EmbeddingProvider
from config.settings import settings
from utils.exceptions import APIRequestError

# nomic-embed-text's output size if that's the model pulled for embeddings;
# override by subclassing/adjusting if you pull a different one.
_DEFAULT_EMBEDDING_DIMENSIONS = 768


class OllamaProvider(ChatProvider, EmbeddingProvider):
    """Talks to a local Ollama server (https://ollama.com) - no API key,
    but it must be installed, running, and have the configured model
    pulled (`ollama pull llama3.1`) before this will work."""

    name = "ollama"
    dimensions = _DEFAULT_EMBEDDING_DIMENSIONS

    def __init__(self):
        self._base_url = settings.OLLAMA_BASE_URL
        self._model = settings.OLLAMA_CHAT_MODEL

    def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> ChatResult:
        try:
            response = requests.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "stream": False,
                    "options": {"temperature": temperature},
                },
                timeout=settings.API_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise APIRequestError(f"Ollama request failed - is it running at {self._base_url}? ({e})") from e

        payload = response.json()
        text = payload.get("message", {}).get("content", "")
        return ChatResult(
            text=text,
            prompt_tokens=payload.get("prompt_eval_count"),
            completion_tokens=payload.get("eval_count"),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Ollama's embeddings endpoint takes one prompt per call.
        vectors = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._model, "prompt": text},
                    timeout=settings.API_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
            except requests.RequestException as e:
                raise APIRequestError(f"Ollama embedding request failed ({e})") from e
            vectors.append(response.json().get("embedding", []))
        return vectors
