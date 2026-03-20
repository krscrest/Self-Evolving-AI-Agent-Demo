import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    AZURE_DOC_INTELLIGENCE_ENDPOINT: str = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT", "")
    AZURE_DOC_INTELLIGENCE_KEY: str = os.getenv("AZURE_DOC_INTELLIGENCE_KEY", "")

    LOGIN_USERNAME: str = os.getenv("LOGIN_USERNAME", "")
    LOGIN_PASSWORD: str = os.getenv("LOGIN_PASSWORD", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")


settings = Settings()

# Validate required settings at startup
_required = {
    "AZURE_OPENAI_ENDPOINT": settings.AZURE_OPENAI_ENDPOINT,
    "AZURE_DOC_INTELLIGENCE_ENDPOINT": settings.AZURE_DOC_INTELLIGENCE_ENDPOINT,
    "SECRET_KEY": settings.SECRET_KEY,
    "LOGIN_USERNAME": settings.LOGIN_USERNAME,
    "LOGIN_PASSWORD": settings.LOGIN_PASSWORD,
}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(_missing)}. "
        "Copy .env.example to .env and fill in all values."
    )
