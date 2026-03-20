from app.services.azure_openai import chat_completion

# Deliberately generic and weak initial prompt to show dramatic improvement
INITIAL_SYSTEM_PROMPT = """You are a helpful AI assistant. Please summarize the following document. 
Provide a brief overview of what the document contains."""


def run_analysis(document_text: str, system_prompt: str) -> str:
    """Run the analyzer agent with the given system prompt against the document text."""
    user_message = f"""Please analyze the following document and provide a comprehensive summary:

---
{document_text}
---"""

    return chat_completion(system_prompt, user_message, temperature=0.2)
