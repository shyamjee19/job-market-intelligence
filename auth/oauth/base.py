from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    provider_id: str
    email: str
    full_name: str | None
