from typing import Any, Dict, List, Optional
from backend.app.teach_back.models import (
    MasteryAssessmentLevel,
    TeachBackAudienceLevel,
)
from backend.app.teach_back.schemas import (
    RubricCriterionScore,
    RubricDimensionDetail,
)


# ==============================================================================
# 1. Standard 5-Criterion Multi-Dimensional Rubric (PRD Cap 17, FR-017)
# ==============================================================================

DEFAULT_RUBRIC_DIMENSIONS: List[RubricDimensionDetail] = [
    RubricDimensionDetail(
        criterion_name="Conceptual Accuracy",
        weight=0.30,
        description="Scientific and physical correctness of principles, laws, definitions, and logical reasoning.",
        max_score=5,
    ),
    RubricDimensionDetail(
        criterion_name="Learning Objective Completeness",
        weight=0.25,
        description="Coverage of essential syllabus learning objectives, boundary conditions, and key variables.",
        max_score=5,
    ),
    RubricDimensionDetail(
        criterion_name="Intuition & Feynman Simplicity",
        weight=0.20,
        description="Clarity of explanation, intuitive physical analogies, and avoidance of empty academic jargon.",
        max_score=5,
    ),
    RubricDimensionDetail(
        criterion_name="Mathematical Rigor & KaTeX",
        weight=0.15,
        description="Correct mathematical formulas, algebraic setup, units, and proper KaTeX LaTeX formatting.",
        max_score=5,
    ),
    RubricDimensionDetail(
        criterion_name="Prerequisite Integration",
        weight=0.10,
        description="Proper foundation and accurate integration of prerequisite concepts without logical leaps.",
        max_score=5,
    ),
]


# ==============================================================================
# 2. Scoring & Classification Functions
# ==============================================================================

def calculate_overall_score(criteria_scores: List[RubricCriterionScore]) -> float:
    """
    Computes normalized weighted composite score (0.0 to 100.0) from rubric criteria scores.
    Formula: Total = (Sum of (score_i / 5.0) * weight_i) / (Sum of weights) * 100.0
    """
    if not criteria_scores:
        return 0.0

    total_weight = sum(c.weight for c in criteria_scores)
    if total_weight <= 0:
        total_weight = 1.0

    weighted_sum = sum((c.score / 5.0) * c.weight for c in criteria_scores)
    composite = (weighted_sum / total_weight) * 100.0
    return round(max(0.0, min(100.0, composite)), 1)


def determine_mastery_level(overall_score: float) -> MasteryAssessmentLevel:
    """
    Maps 0-100 composite score to pedagogical mastery tier.
    """
    if overall_score >= 85.0:
        return MasteryAssessmentLevel.MASTERED
    elif overall_score >= 70.0:
        return MasteryAssessmentLevel.COMPETENT
    elif overall_score >= 50.0:
        return MasteryAssessmentLevel.DEVELOPING
    else:
        return MasteryAssessmentLevel.NEEDS_REVIEW


# ==============================================================================
# 3. Dynamic Prompt Generation
# ==============================================================================

def get_audience_instructions(audience_level: TeachBackAudienceLevel) -> str:
    if audience_level == TeachBackAudienceLevel.CHILD_10YO:
        return (
            "TARGET AUDIENCE: A curious 10-year-old child (Feynman Mode).\n"
            "- Reward intuitive, real-world analogies (e.g. toy cars, water pipes, playground swings).\n"
            "- Heavily penalize unexplained academic jargon or memorized textbook phrases.\n"
            "- Praise simple, vivid explanations of complex concepts."
        )
    elif audience_level == TeachBackAudienceLevel.UNDERGRAD_EXAMINER:
        return (
            "TARGET AUDIENCE: Cambridge / University Academic Examiner.\n"
            "- Demand formal mathematical rigor, boundary conditions, and precise physical definitions.\n"
            "- Verify exact formula notations ($...$, $$...$$) and algebraic conditions."
        )
    else:
        return (
            "TARGET AUDIENCE: High School Peer Study Partner (Standard Mode).\n"
            "- Expect clear, approachable communication balancing intuition with standard syllabus terminology and algebra."
        )


def build_rubric_system_prompt(
    topic_title: str,
    topic_description: str,
    learning_objectives: List[Dict[str, Any]],
    prerequisites: List[Dict[str, Any]],
    audience_level: TeachBackAudienceLevel,
    grounded_chunks: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Assembles a comprehensive, curriculum-grounded LLM system prompt for Teach-Back evaluation.
    Enforces KaTeX formatting and multi-criterion rubric invariants.
    """
    objectives_text = "\n".join(
        f"- [{obj.get('code', 'LO')}] {obj.get('description', '')}"
        + (f" (Formula: ${obj.get('formula_latex')}$)" if obj.get('formula_latex') else "")
        for obj in learning_objectives
    ) or "- Understand the core principles and laws of this syllabus topic."

    prerequisites_text = "\n".join(
        f"- [Prereq ID: {p.get('id', 'N/A')}] {p.get('title', 'Foundational Topic')}: {p.get('description', '')}"
        for p in prerequisites
    ) or "- Foundational high school algebra, calculus, and scientific principles."

    sources_block = ""
    if grounded_chunks:
        formatted_chunks = "\n---\n".join(
            f"Source [{c.get('source_title', 'Textbook')}]: {c.get('content', '')}"
            for c in grounded_chunks
        )
        sources_block = f"\n### GROUNDED TEXTBOOK SOURCES:\n{formatted_chunks}\n"

    audience_text = get_audience_instructions(audience_level)

    prompt = f"""You are an elite, encouraging, and rigorous Senior Pedagogical Evaluator for the Feynman Adaptive Learning Platform.

Your task is to evaluate a student's explanation in "Teach-Back Mode" (Feynman Technique).

### EVALUATION CONTEXT:
- **Topic Under Review:** {topic_title}
- **Topic Overview:** {topic_description}
- **Target Audience Level:** {audience_level.value}

### OFFICIAL SYLLABUS LEARNING OBJECTIVES:
{objectives_text}

### SYLLABUS PREREQUISITE CONCEPTS:
{prerequisites_text}
{sources_block}
### AUDIENCE SCAFFOLDING GUIDELINES:
{audience_text}

### EVALUATION RUBRIC CRITERIA (Score 1 to 5 for each):
1. **Conceptual Accuracy (Weight: 0.30):** Is the physics/mathematics factually true? Are there any false assumptions or flawed logical leaps?
2. **Learning Objective Completeness (Weight: 0.25):** Did the explanation cover the necessary syllabus objectives and critical variables?
3. **Intuition & Feynman Simplicity (Weight: 0.20):** Did the student explain the concept simply using intuitive mental models, or did they rely on memorized jargon?
4. **Mathematical Rigor & KaTeX (Weight: 0.15):** Are formulas written correctly using KaTeX notation ($...$ or $$...$$)? Are units and variables clear?
5. **Prerequisite Integration (Weight: 0.10):** Did the student build on prerequisite foundations properly?

### OUTPUT INSTRUCTIONS:
- You must evaluate strictly and constructively.
- Identify at least 1-2 authentic strengths.
- If there are misconceptions or false statements, pinpoint them explicitly.
- If prerequisite concepts were misused or missing, map them to the relevant prerequisite topic.
- Provide clear pedagogical feedback and an optional KaTeX-formatted model correction snippet.
"""
    return prompt
