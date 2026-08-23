from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.advanced_modes.models import (
    AdversarialSessionStatus,
    DefenseOutcome,
    FallacyCategory,
)


# ==============================================================================
# 1. Adversarial Mode Schemas (PRD Cap 18, FR-018)
# ==============================================================================

class AdversarialChallengeRequest(BaseModel):
    exam_template_id: str = Field(..., description="Target exam curriculum ID")
    topic_id: str = Field(..., description="Target syllabus topic ID")
    student_thesis: str = Field(
        ...,
        min_length=15,
        max_length=5000,
        description="Student conceptual claim, reasoning chain, or physics law formulation to be stress-tested",
    )


class AdversarialChallengeOutput(BaseModel):
    """
    LLM structured output validation target for counterexample generation.
    """
    counterexample_title: str = Field(..., description="Concise, vivid title of the edge-case challenge")
    counterexample_scenario: str = Field(..., description="Detailed physical scenario where the student claim breaks down")
    edge_case_condition: str = Field(..., description="Specific perturbed parameter or boundary condition (e.g. friction -> 0)")
    challenge_question: str = Field(..., description="Direct Socratic challenge question demanding defense or adaptation")
    underlying_principle: str = Field(..., description="The fundamental law or theorem at play")


class AdversarialChallengeResponse(BaseModel):
    session_id: str
    challenge_id: str
    topic_id: str
    student_thesis: str
    counterexample_title: str
    counterexample_scenario: str
    edge_case_condition: str
    challenge_question: str
    created_at: datetime


class AdversarialDefendRequest(BaseModel):
    session_id: str = Field(..., description="Active adversarial sparring session ID")
    challenge_id: str = Field(..., description="Specific challenge being responded to")
    student_defense: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Student defense, mathematical justification, or thesis refinement",
    )


class DefenseEvaluationOutput(BaseModel):
    """
    LLM structured output validation target for student defense scoring.
    """
    robustness_score: float = Field(..., ge=0.0, le=100.0, description="Evaluated defense score 0-100")
    defense_outcome: DefenseOutcome = Field(..., description="Categorized outcome of the sparring round")
    valid_points: List[str] = Field(default=[], description="Correct physical principles or valid arguments raised by student")
    logical_flaws: List[str] = Field(default=[], description="Remaining misconceptions, contradictions, or unaddressed conditions")
    feedback: str = Field(..., description="Encouraging pedagogical commentary on the defense")
    model_synthesis_latex: Optional[str] = Field(
        default=None,
        description="Comprehensive, unified model synthesis with KaTeX formulas",
    )


class DefenseEvaluationResponse(BaseModel):
    session_id: str
    challenge_id: str
    robustness_score: float = Field(..., ge=0.0, le=100.0)
    defense_outcome: DefenseOutcome
    valid_points: List[str] = []
    logical_flaws: List[str] = []
    feedback: str
    model_synthesis_latex: Optional[str] = None
    evaluated_at: datetime


class AdversarialChallengeSummary(BaseModel):
    id: str
    counterexample_title: str
    counterexample_scenario: str
    edge_case_condition: str
    challenge_question: str
    student_defense: Optional[str] = None
    robustness_score: Optional[float] = None
    defense_outcome: Optional[DefenseOutcome] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdversarialSessionDetailResponse(BaseModel):
    id: str
    student_id: str
    exam_template_id: str
    topic_id: str
    student_thesis: str
    status: AdversarialSessionStatus
    challenges: List[AdversarialChallengeSummary] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdversarialSessionListResponse(BaseModel):
    sessions: List[AdversarialSessionDetailResponse] = []
    total: int = 0


# ==============================================================================
# 2. Why-You-Are-Wrong Diagnostic Schemas (PRD Cap 19, FR-019)
# ==============================================================================

class WhyWrongDiagnosticRequest(BaseModel):
    topic_id: str = Field(..., description="Target syllabus topic ID")
    question_id: Optional[str] = Field(None, description="Optional question bank ID")
    question_prompt: str = Field(..., min_length=10, description="Full problem prompt or question context")
    selected_option_key: Optional[str] = Field(None, max_length=10, description="Option letter if MCQ (e.g. 'B')")
    selected_answer_text: str = Field(..., min_length=3, description="The incorrect option text or student answer")
    correct_answer_text: Optional[str] = Field(None, description="The correct answer text if available")


class WhyWrongDiagnosticOutput(BaseModel):
    """
    LLM structured output validation target for causal fallacy breakdown.
    """
    fallacy_category: FallacyCategory = Field(..., description="Formal cognitive fallacy classification")
    why_incorrect_explanation: str = Field(..., description="Step-by-step scientific proof of why this choice fails")
    mental_trap_description: str = Field(..., description="The psychological bias or intuitive trap that lured the student")
    recognition_rule: str = Field(..., description="Actionable mental decision heuristic for future questions")
    repair_action_summary: str = Field(..., description="Concrete revision micro-practice recommendation")
    correct_derivation_latex: Optional[str] = Field(
        default=None,
        description="Correct step-by-step mathematical derivation in KaTeX",
    )


class WhyWrongDiagnosticResponse(BaseModel):
    id: str
    topic_id: str
    question_id: Optional[str] = None
    selected_option_key: Optional[str] = None
    selected_answer_text: str
    fallacy_category: FallacyCategory
    why_incorrect_explanation: str
    mental_trap_description: str
    recognition_rule: str
    repair_action_summary: str
    correct_derivation_latex: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
