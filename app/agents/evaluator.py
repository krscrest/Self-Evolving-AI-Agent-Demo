import json
from app.services.azure_openai import chat_completion

EVALUATOR_SYSTEM_PROMPT = """You are a strict Certificate of Insurance (CoI) document analysis evaluator. 
Your job is to score an AI-generated summary of a CoI document against a detailed rubric.

You must evaluate the summary against the ORIGINAL DOCUMENT TEXT to check completeness and accuracy.

## Scoring Rubric (100 points total)

| Category | Max Points | Criteria |
|----------|-----------|----------|
| Named Insured | 10 | Full legal name, DBA if applicable, complete address |
| Policy Numbers | 10 | ALL policy numbers listed in the document are captured |
| Insurance Carrier | 10 | All insurer/carrier names, NAIC numbers if present |
| Coverage Types | 10 | All coverage types identified (GL, Auto, Umbrella, WC, etc.) |
| Coverage Limits | 15 | Per-occurrence, aggregate, and per-policy limits for EACH coverage |
| Effective & Expiration Dates | 10 | Start/end dates for EACH policy listed |
| Certificate Holder | 10 | Full name, address, and relationship to insured |
| Additional Insured | 10 | Whether additional insured is indicated, for which policies |
| Subrogation Waiver | 5 | Whether waiver of subrogation applies and to which policies |
| Special Conditions | 10 | Any endorsements, exclusions, or special provisions noted |

## Scoring Guidelines
- Award FULL points only if the category is completely and accurately covered
- Award PARTIAL points if some but not all information is present
- Award ZERO points if the category is completely missing
- Be strict but fair — the goal is to drive real improvement

## Output Format
You MUST respond with ONLY a valid JSON object (no markdown, no explanation outside JSON):
{
    "named_insured": <0-10>,
    "policy_numbers": <0-10>,
    "insurance_carrier": <0-10>,
    "coverage_types": <0-10>,
    "coverage_limits": <0-15>,
    "effective_expiration_dates": <0-10>,
    "certificate_holder": <0-10>,
    "additional_insured": <0-10>,
    "subrogation_waiver": <0-5>,
    "special_conditions": <0-10>,
    "total": <sum of above>,
    "feedback": "<2-3 sentences describing what was missed or done poorly, and what specific improvements would increase the score>"
}"""


def evaluate_summary(document_text: str, summary: str) -> dict:
    """Evaluate a CoI summary against the rubric. Returns a score dictionary."""
    user_message = f"""## Original Document
{document_text}

## AI-Generated Summary to Evaluate
{summary}

Score this summary against the rubric. Be strict and specific in your feedback."""

    response = chat_completion(EVALUATOR_SYSTEM_PROMPT, user_message, temperature=0.1)

    # Parse JSON from response, handling potential markdown wrapping
    response = response.strip()
    if response.startswith("```"):
        lines = response.split("\n")
        response = "\n".join(lines[1:-1])

    try:
        scores = json.loads(response)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from the response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            scores = json.loads(response[start:end])
        else:
            scores = {
                "named_insured": 0, "policy_numbers": 0, "insurance_carrier": 0,
                "coverage_types": 0, "coverage_limits": 0, "effective_expiration_dates": 0,
                "certificate_holder": 0, "additional_insured": 0, "subrogation_waiver": 0,
                "special_conditions": 0, "total": 0,
                "feedback": "Error: Could not parse evaluator response."
            }

    # Ensure total is calculated correctly
    score_fields = [
        "named_insured", "policy_numbers", "insurance_carrier", "coverage_types",
        "coverage_limits", "effective_expiration_dates", "certificate_holder",
        "additional_insured", "subrogation_waiver", "special_conditions"
    ]
    scores["total"] = sum(scores.get(f, 0) for f in score_fields)

    return scores
