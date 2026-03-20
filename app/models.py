from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str


class CycleScore(BaseModel):
    named_insured: int = 0
    policy_numbers: int = 0
    insurance_carrier: int = 0
    coverage_types: int = 0
    coverage_limits: int = 0
    effective_expiration_dates: int = 0
    certificate_holder: int = 0
    additional_insured: int = 0
    subrogation_waiver: int = 0
    special_conditions: int = 0
    total: int = 0
    feedback: str = ""


class CycleResult(BaseModel):
    cycle_number: int
    system_prompt: str
    summary_output: str
    score: CycleScore
    improved_prompt: Optional[str] = None


class OptimizationEvent(BaseModel):
    event_type: str  # "log", "cycle_start", "summary", "score", "prompt_update", "complete"
    cycle_number: int = 0
    data: dict = {}
