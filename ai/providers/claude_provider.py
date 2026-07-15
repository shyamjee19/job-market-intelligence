from anthropic import Anthropic

from ai.providers.base import ChatMessage, ChatProvider, ChatResult, EmbeddingProvider
from config.settings import settings
from utils.exceptions import APIRequestError

_MAX_TOKENS = 1024


class ClaudeProvider(ChatProvider):
    """Chat only - Anthropic has no embeddings API. Set
    AI_EMBEDDING_PROVIDER to a different provider (default: openai) to use
    Claude for chat while something else handles embeddings."""

    name = "claude"

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise APIRequestError("ANTHROPIC_API_KEY is not set")
        self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._model = settings.ANTHROPIC_CHAT_MODEL

    def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> ChatResult:
        # Anthropic takes the system prompt as its own top-level field,
        # not as a message in the conversation list like OpenAI does.
        system_prompt = "\n".join(m.content for m in messages if m.role == "system")
        turns = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]

        response = self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            system=system_prompt,
            messages=turns,
            temperature=temperature,
        )
        text = response.content[0].text if response.content else ""
        return ChatResult(
            text=text,
            prompt_tokens=response.usage.input_tokens if response.usage else None,
            completion_tokens=response.usage.output_tokens if response.usage else None,
        )


class ClaudeEmbeddingUnavailable(EmbeddingProvider):
    """Placeholder that fails loudly and explains why, rather than the
    registry silently picking something unexpected if AI_EMBEDDING_PROVIDER
    is ever misconfigured to "claude"."""

    name = "claude"
    dimensions = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "Anthropic has no embeddings API. Set AI_EMBEDDING_PROVIDER=openai "
            "(or another embedding-capable provider) in .env."
        )
