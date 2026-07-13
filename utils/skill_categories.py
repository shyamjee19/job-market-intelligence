"""Keyword-based categorization of skill/tag strings into AI, Cloud, and
general Tech buckets for the dashboard's skills breakdown. A tag can match
more than one category (e.g. "mlops" is both AI and Cloud)."""
import re

AI_KEYWORDS = [
    "ai", "ml", "machine learning", "deep learning", "llm", "gpt", "nlp",
    "artificial intelligence", "data science", "genai", "generative ai",
    "computer vision", "neural", "pytorch", "tensorflow", "mlops",
]

CLOUD_KEYWORDS = [
    "aws", "azure", "gcp", "cloud", "kubernetes", "k8s", "docker",
    "terraform", "devops", "serverless", "google cloud",
]

TECH_KEYWORDS = [
    "python", "java", "javascript", "typescript", "react", "node",
    "sql", "golang", "go", "rust", "c++", "c#", "php", "ruby", "swift",
    "kotlin", "scala", "web dev", "mobile", "backend", "frontend",
    "full stack", "api", "database", "microservices", "linux",
]


def _compile_keyword(keyword: str) -> re.Pattern:
    """Word-boundary match for plain alphanumeric keywords ("ai" won't
    match inside "training" or "teamleitung"). Keywords with symbols
    (e.g. "c++", "c#") fall back to a plain substring match, since \\b
    doesn't work cleanly around non-word characters and those symbols are
    distinctive enough not to false-positive."""
    if re.fullmatch(r"[\w\s]+", keyword):
        return re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
    return re.compile(re.escape(keyword), re.IGNORECASE)


def _compile_all(keywords: list[str]) -> list[re.Pattern]:
    return [_compile_keyword(k) for k in keywords]


_AI_PATTERNS = _compile_all(AI_KEYWORDS)
_CLOUD_PATTERNS = _compile_all(CLOUD_KEYWORDS)
_TECH_PATTERNS = _compile_all(TECH_KEYWORDS)


def _matches(tag: str, patterns: list[re.Pattern]) -> bool:
    return any(pattern.search(tag) for pattern in patterns)


def is_ai_skill(tag: str) -> bool:
    return _matches(tag, _AI_PATTERNS)


def is_cloud_skill(tag: str) -> bool:
    return _matches(tag, _CLOUD_PATTERNS)


def is_tech_skill(tag: str) -> bool:
    return _matches(tag, _TECH_PATTERNS)


CATEGORY_MATCHERS = {
    "ai": is_ai_skill,
    "cloud": is_cloud_skill,
    "tech": is_tech_skill,
}
