from app.services.azure_openai import chat_completion

OPTIMIZER_SYSTEM_PROMPT = """You are an expert prompt engineer specializing in optimizing system prompts for AI agents.

Your task: Given a current system prompt and evaluation feedback, write an IMPROVED system prompt that will produce better results on the next run.

## Rules for Prompt Optimization
1. The improved prompt must be a COMPLETE system prompt (not a patch or diff)
2. Address EVERY piece of feedback from the evaluator
3. Add specific extraction instructions for categories that scored low
4. Include output format guidance (structured sections, tables, etc.)
5. Add domain-specific terminology and expertise framing
6. Keep the prompt focused and under 500 words
7. Each iteration should build on previous improvements, not start from scratch
8. Frame the agent as a domain expert with specific skills

## Output Format
Respond with ONLY the new system prompt text. No explanation, no markdown headers, no quotes around it. 
Just the raw system prompt that will be used directly."""


def optimize_prompt(current_prompt: str, evaluation_feedback: dict, cycle_number: int) -> str:
    """Generate an improved system prompt based on evaluation feedback."""
    score_breakdown = "\n".join(
        f"  - {k.replace('_', ' ').title()}: {v}/{max_pts}"
        for k, (v, max_pts) in {
            "named_insured": (evaluation_feedback.get("named_insured", 0), 10),
            "policy_numbers": (evaluation_feedback.get("policy_numbers", 0), 10),
            "insurance_carrier": (evaluation_feedback.get("insurance_carrier", 0), 10),
            "coverage_types": (evaluation_feedback.get("coverage_types", 0), 10),
            "coverage_limits": (evaluation_feedback.get("coverage_limits", 0), 15),
            "effective_expiration_dates": (evaluation_feedback.get("effective_expiration_dates", 0), 10),
            "certificate_holder": (evaluation_feedback.get("certificate_holder", 0), 10),
            "additional_insured": (evaluation_feedback.get("additional_insured", 0), 10),
            "subrogation_waiver": (evaluation_feedback.get("subrogation_waiver", 0), 5),
            "special_conditions": (evaluation_feedback.get("special_conditions", 0), 10),
        }.items()
    )

    user_message = f"""## Current System Prompt (Cycle {cycle_number})
{current_prompt}

## Evaluation Results
Total Score: {evaluation_feedback.get('total', 0)}/100
Score Breakdown:
{score_breakdown}

## Evaluator Feedback
{evaluation_feedback.get('feedback', 'No specific feedback provided.')}

## Task
Write an improved system prompt that specifically addresses the weak areas identified above. 
The improved prompt should help the AI agent extract and present ALL required information from Certificate of Insurance documents."""

    return chat_completion(OPTIMIZER_SYSTEM_PROMPT, user_message, temperature=0.4)
