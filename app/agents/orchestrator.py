import json
import asyncio
from typing import AsyncGenerator
from app.agents.analyzer import INITIAL_SYSTEM_PROMPT, run_analysis
from app.agents.evaluator import evaluate_summary
from app.agents.optimizer import optimize_prompt


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def run_optimization_loop(document_text: str, num_cycles: int = 3) -> AsyncGenerator[str, None]:
    """
    Run the full optimization loop and yield SSE events.
    
    Cycles: 0 (baseline), 1 (first optimization), 2 (second optimization)
    """
    current_prompt = INITIAL_SYSTEM_PROMPT
    results = []

    yield _sse_event("start", {
        "message": "Starting Auto-Prompt Optimization",
        "total_cycles": num_cycles,
        "initial_prompt": current_prompt
    })

    for cycle in range(num_cycles):
        # --- Cycle Start ---
        yield _sse_event("cycle_start", {
            "cycle": cycle,
            "prompt": current_prompt,
            "message": f"Cycle {cycle}: Running analysis with {'initial generic' if cycle == 0 else 'optimized'} prompt..."
        })

        # Small delay to let the UI render
        await asyncio.sleep(0.5)

        # --- Step 1: Analyze ---
        yield _sse_event("log", {
            "cycle": cycle,
            "step": "analyze",
            "message": f"Cycle {cycle}: Analyzer agent processing document..."
        })

        # Run in thread pool to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(None, run_analysis, document_text, current_prompt)

        yield _sse_event("summary", {
            "cycle": cycle,
            "summary": summary,
            "message": f"Cycle {cycle}: Analysis complete. Evaluating quality..."
        })

        await asyncio.sleep(0.3)

        # --- Step 2: Evaluate ---
        yield _sse_event("log", {
            "cycle": cycle,
            "step": "evaluate",
            "message": f"Cycle {cycle}: Evaluator agent scoring against rubric..."
        })

        scores = await loop.run_in_executor(None, evaluate_summary, document_text, summary)

        yield _sse_event("score", {
            "cycle": cycle,
            "scores": scores,
            "message": f"Cycle {cycle}: Score = {scores.get('total', 0)}/100"
        })

        await asyncio.sleep(0.3)

        # --- Step 3: Optimize (skip on last cycle) ---
        improved_prompt = None
        if cycle < num_cycles - 1:
            yield _sse_event("log", {
                "cycle": cycle,
                "step": "optimize",
                "message": f"Cycle {cycle}: Optimizer agent rewriting system prompt based on feedback..."
            })

            improved_prompt = await loop.run_in_executor(
                None, optimize_prompt, current_prompt, scores, cycle
            )

            yield _sse_event("prompt_update", {
                "cycle": cycle,
                "old_prompt": current_prompt,
                "new_prompt": improved_prompt,
                "message": f"Cycle {cycle}: System prompt rewritten. Moving to Cycle {cycle + 1}..."
            })

            current_prompt = improved_prompt
        else:
            yield _sse_event("log", {
                "cycle": cycle,
                "step": "complete",
                "message": f"Cycle {cycle}: Final cycle complete. No further optimization needed."
            })

        results.append({
            "cycle": cycle,
            "prompt": current_prompt if improved_prompt is None else scores.get("feedback", ""),
            "summary": summary,
            "scores": scores,
            "improved_prompt": improved_prompt
        })

        await asyncio.sleep(0.3)

    # --- Final Summary ---
    score_progression = [r["scores"]["total"] for r in results]
    improvement = score_progression[-1] - score_progression[0]

    yield _sse_event("complete", {
        "message": f"Optimization complete! Score improved from {score_progression[0]} to {score_progression[-1]} (+{improvement} points)",
        "score_progression": score_progression,
        "total_improvement": improvement,
        "cycles": len(results)
    })
