from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from app.config import settings

# Create a token provider for Azure OpenAI using Entra ID
_credential = DefaultAzureCredential()
_token_provider = get_bearer_token_provider(
    _credential, "https://cognitiveservices.azure.com/.default"
)


def get_client() -> AzureOpenAI:
    """Create and return an Azure OpenAI client using Entra ID authentication."""
    return AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        azure_ad_token_provider=_token_provider,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )


def chat_completion(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    """Run a chat completion with the given system prompt and user message."""
    client = get_client()
    response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""
