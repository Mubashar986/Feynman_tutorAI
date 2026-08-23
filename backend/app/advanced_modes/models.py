from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel


# ==============================================================================
# 1. Enums: Defense Outcomes & Cognitive Fallacy Categories (PRD Cap 18, 19)
# ==============================================================================

class DefenseOutcome(str, Enum):
    """
    Evaluated outcome of a student's defense against an adversarial counterexample.
    """
    DEFENDED_SUCCESSFULLY = "defended_successfully"  # Stood firm with correct physical/mathematical justification
    VALID_ADAPTATION = "valid_adaptation"            # Appropriately recognized the boundary condition limit and refined thesis
    PARTIAL_CONCESSION = "partial_concession"        # Partially acknowledged error but left logical gaps
    LOGICAL_COLLAPSE = "logical_collapse"            # Failed to defend or introduced contradictory falsehoods


class FallacyCategory(str, Enum):
    """
    Formal 7-Tier Cognitive Fallacy Taxonomy for STEM and Exam Problem Solving (PRD FR-019).
    """
    BOUNDARY_CONDITION_BLINDNESS = "boundary_condition_blindness"  # Assuming localized formulas apply at extreme limits
    FORMULA_MISAPPLICATION = "formula_misapplication"              # Using formulas outside valid assumptions (e.g. constant a equations for variable a)
    INVERSE_RELATION_CONFUSION = "inverse_relation_confusion"      # Confusing direct with inverse or inverse-square proportionality
    STATE_VS_RATE_CONFUSION = "state_vs_rate_confusion"            # Confusing an instantaneous state (e.g. position, velocity) with its derivative (acceleration)
    SIGN_VECTOR_INVERSION = "sign_vector_inversion"                # Forgetting directionality, work signs, or coordinate conventions
    ASSUMPTION_VIOLATION = "assumption_violation"                  # Neglecting key system constraints (e.g. friction, non-isolated systems)
    UNITS_DIMENSIONAL_ERROR = "units_dimensional_error"            # Inconsistent units, scalar vs vector addition, or dimensional mismatch


class AdversarialSessionStatus(str, Enum):
    """
    Lifecycle state for an adversarial sparring debate.
    """
    CHALLENGE_ACTIVE = "challenge_active"
    DEFENDED = "defended"
    CONCLUDED = "concluded"


# ==============================================================================
# 2. Database Models: Adversarial Sparring & Cognitive Diagnostics
# ==============================================================================

class AdversarialSessionBase(SQLModel):
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True, nullable=False)
    topic_id: str = Field(foreign_key="topics.id", index=True, nullable=False)
    student_thesis: str = Field(nullable=False, description="Initial student thesis, rule claim, or reasoning statement")
    status: AdversarialSessionStatus = Field(
        default=AdversarialSessionStatus.CHALLENGE_ACTIVE,
        nullable=False,
    )


class AdversarialSession(AdversarialSessionBase, table=True):
    """
    Multi-turn state boundary for Adversarial Sparring dialogues (PRD Cap 18, FR-018).
    Enforces student-exam isolation (Constraint #2).
    """
    __tablename__ = "adversarial_sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )


class AdversarialChallengeBase(SQLModel):
    session_id: str = Field(foreign_key="adversarial_sessions.id", index=True, nullable=False)
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    counterexample_title: str = Field(nullable=False, max_length=200)
    counterexample_scenario: str = Field(nullable=False, description="Concrete physical/mathematical scenario challenging thesis")
    edge_case_condition: str = Field(nullable=False, description="Specific perturbed boundary condition (e.g. friction -> 0, v -> c)")
    challenge_question: str = Field(nullable=False, description="Socratic challenge prompt demanding defense or clarification")
    student_defense: Optional[str] = Field(default=None, description="Student defense or rebuttal response")
    robustness_score: Optional[float] = Field(default=None, description="Defense score from 0.0 to 100.0")
    defense_outcome: Optional[DefenseOutcome] = Field(default=None)
    feedback: Optional[str] = Field(default=None, description="Constructive pedagogical review of student defense")


class AdversarialChallenge(AdversarialChallengeBase, table=True):
    """
    Individual challenge turn within an adversarial sparring session.
    """
    __tablename__ = "adversarial_challenges"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )


class WhyWrongDiagnosticBase(SQLModel):
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    question_id: Optional[str] = Field(default=None, foreign_key="questions.id", index=True)
    topic_id: str = Field(foreign_key="topics.id", index=True, nullable=False)
    selected_option_key: Optional[str] = Field(default=None, max_length=10, description="Selected MCQ option letter if applicable")
    selected_answer_text: str = Field(nullable=False, description="Incorrect student choice or conceptual fallacy text")
    fallacy_category: FallacyCategory = Field(default=FallacyCategory.FORMULA_MISAPPLICATION, nullable=False)
    why_incorrect_explanation: str = Field(nullable=False, description="Scientific breakdown of why this selection fails")
    mental_trap_description: str = Field(nullable=False, description="Cognitive bias or intuitive trap that lured the student")
    recognition_rule: str = Field(nullable=False, description="Actionable mental decision heuristic for future questions")
    repair_action_summary: str = Field(nullable=False, description="Targeted micro-practice or revision task")


class WhyWrongDiagnostic(WhyWrongDiagnosticBase, table=True):
    """
    Diagnostic flaw decomposition record for an incorrect answer (PRD Cap 19, FR-019).
    Feeds directly into the Error Bank and personal learning profile.
    """
    __tablename__ = "why_wrong_diagnostics"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
