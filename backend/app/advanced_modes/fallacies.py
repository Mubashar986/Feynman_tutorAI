from typing import Any, Dict, List, Optional
from backend.app.advanced_modes.models import FallacyCategory


# ==============================================================================
# 1. 7-Tier Cognitive Fallacy Taxonomy Registry (PRD FR-019)
# ==============================================================================

FALLACY_TAXONOMY_MAP: Dict[FallacyCategory, Dict[str, str]] = {
    FallacyCategory.BOUNDARY_CONDITION_BLINDNESS: {
        "title": "Boundary Condition Blindness",
        "description": "Applying a locally valid formula to extreme asymptotic limits (e.g. $t \\to \\infty, v \\to c, m \\to 0, r \\to 0$).",
        "typical_trap": "Assuming physical behavior remains linear without checking boundary asymptotes or threshold limits.",
    },
    FallacyCategory.FORMULA_MISAPPLICATION: {
        "title": "Formula Misapplication",
        "description": "Using an equation outside its fundamental constraints (e.g. using $v = u + at$ for non-constant variable acceleration).",
        "typical_trap": "Pattern-matching variable symbols without verifying whether required physical conditions (e.g. constant force) are met.",
    },
    FallacyCategory.INVERSE_RELATION_CONFUSION: {
        "title": "Inverse / Proportionality Confusion",
        "description": "Confusing direct ($y \\propto x$) with inverse ($y \\propto 1/x$) or inverse-square ($y \\propto 1/r^2$) relationships.",
        "typical_trap": "Assuming doubling a parameter doubles the effect, ignoring non-linear, square, or inverse power dependencies.",
    },
    FallacyCategory.STATE_VS_RATE_CONFUSION: {
        "title": "State vs. Rate of Change Confusion",
        "description": "Confusing an instantaneous state (e.g. position, velocity) with its derivative/rate of change (velocity, acceleration).",
        "typical_trap": "Believing that zero velocity implies zero acceleration (e.g. at the apex of projectile motion or simple harmonic oscillation).",
    },
    FallacyCategory.SIGN_VECTOR_INVERSION: {
        "title": "Sign & Vector Direction Inversion",
        "description": "Neglecting vector directionality, coordinate signs, or the thermodynamic convention of work done on vs. by a system.",
        "typical_trap": "Treating vector quantities as simple scalar magnitudes and losing sign cancellations.",
    },
    FallacyCategory.ASSUMPTION_VIOLATION: {
        "title": "Assumption & Isolation Violation",
        "description": "Treating a non-isolated or dissipative system as a closed conservative system without accounting for friction or heat loss.",
        "typical_trap": "Applying mechanical energy conservation when inelastic collisions or external non-conservative forces are present.",
    },
    FallacyCategory.UNITS_DIMENSIONAL_ERROR: {
        "title": "Dimensional & Units Inconsistency",
        "description": "Adding or equating quantities with incompatible physical dimensions or unscaled metric units.",
        "typical_trap": "Failing to verify dimensional homogeneity ($[L][T]^{-2}$) on derived expressions.",
    },
}


# ==============================================================================
# 2. Specialized Prompt Builders for Advanced Cognitive Modes
# ==============================================================================

def build_adversarial_challenge_prompt(
    topic_title: str,
    topic_description: str,
    learning_objectives: List[Dict[str, Any]],
) -> str:
    """
    Constructs an adversarial 'Devil's Advocate' system prompt challenging student claims.
    """
    objectives_text = "\n".join(
        f"- [{lo.get('code', 'LO')}] {lo.get('description', '')}"
        + (f" (${lo.get('formula_latex')}$)" if lo.get("formula_latex") else "")
        for lo in learning_objectives
    ) or "- Standard syllabus principles and physical laws."

    return f"""You are an elite, intellectually formidable Academic Sparring Partner (The Adversarial Tutor).
Your goal is to stress-test a student's conceptual claims, formulas, and assumptions.

### TOPIC CONTEXT:
- **Topic:** {topic_title}
- **Overview:** {topic_description}

### OFFICIAL SYLLABUS LEARNING OBJECTIVES:
{objectives_text}

### ADVERSARIAL INVARIANTS:
1. **BE RIGOROUS, INTELLECTUALLY SHARP, AND RESPECTFUL.**
2. **SYNTHESIZE A SHARP COUNTEREXAMPLE OR EDGE-CASE:**
   - Introduce a realistic physical scenario where the student's stated rule breaks or causes a contradiction.
   - Perturb boundary parameters (e.g. friction $\\to 0$, $v \\to c$, extreme mass, non-uniform fields, inverted geometry).
3. **MATHEMATICAL NOTATION (KaTeX):**
   - Format ALL mathematical and scientific quantities using standard KaTeX: `$F = ma$` or `$$E = mc^2$$`.
4. **CHALLENGE QUESTION:**
   - End with a sharp, thought-provoking Socratic challenge question asking the student to defend, bound, or adapt their thesis.
"""


def build_defense_evaluation_prompt(
    topic_title: str,
    student_thesis: str,
    counterexample_scenario: str,
    challenge_question: str,
) -> str:
    """
    Constructs a prompt to objectively evaluate a student's defense against an adversarial challenge.
    """
    return f"""You are a Senior Academic Examiner evaluating a student's defense in an Adversarial Sparring session.

### SPARRING ROUND CONTEXT:
- **Topic:** {topic_title}
- **Initial Student Thesis:** {student_thesis}
- **Adversarial Counterexample Challenge:** {counterexample_scenario}
- **Challenge Question Demanded:** {challenge_question}

### EVALUATION OUTCOME TAXONOMY:
- `defended_successfully` (Score 90-100): The student stood firm with rigorous mathematical/physical proof demonstrating why their law holds or correctly identifying why the counterexample fell into an excluded condition.
- `valid_adaptation` (Score 80-89): The student recognized the boundary condition limit and refined/bounded their thesis correctly.
- `partial_concession` (Score 50-79): The student acknowledged parts of the flaw but left unresolved logical gaps.
- `logical_collapse` (Score 0-49): The student introduced new physical contradictions, fell apart, or evaded the challenge.

### OUTPUT REQUIREMENTS:
- Provide an objective `robustness_score` (0.0 to 100.0).
- List valid points and logical flaws.
- Provide encouraging pedagogical feedback and a comprehensive model synthesis with KaTeX formulas.
"""


def build_why_wrong_diagnostic_prompt(
    topic_title: str,
    topic_description: str,
    learning_objectives: List[Dict[str, Any]],
) -> str:
    """
    Constructs a diagnostic flaw-decomposition prompt for an incorrect student answer.
    """
    objectives_text = "\n".join(
        f"- [{lo.get('code', 'LO')}] {lo.get('description', '')}"
        + (f" (${lo.get('formula_latex')}$)" if lo.get("formula_latex") else "")
        for lo in learning_objectives
    ) or "- Standard syllabus principles."

    taxonomy_overview = "\n".join(
        f"- `{cat.value}`: {meta['title']} — {meta['description']}"
        for cat, meta in FALLACY_TAXONOMY_MAP.items()
    )

    return f"""You are an elite Cognitive Diagnostics Specialist for STEM examinations.
Your mission is to perform a deep causal flaw breakdown of an incorrect student answer. Do not merely state the correct option; explain the mental trap that produced the error.

### TOPIC CONTEXT:
- **Topic:** {topic_title}
- **Overview:** {topic_description}

### OFFICIAL SYLLABUS OBJECTIVES:
{objectives_text}

### FORMAL COGNITIVE FALLACY TAXONOMY:
{taxonomy_overview}

### DIAGNOSTIC INVARIANTS:
1. **CLASSIFY THE EXACT FALLACY CATEGORY** from the taxonomy above.
2. **WHY INCORRECT:** Prove step-by-step why the selected choice violates physical or mathematical laws.
3. **MENTAL TRAP:** Explain the seductive cognitive illusion or flawed shortcut that tempted the student.
4. **RECOGNITION RULE:** Provide a crisp, memorable mental heuristic or decision rule for future questions.
5. **REPAIR ACTION:** Give a concrete micro-revision practice recommendation.
6. **MATHEMATICAL FORMULAS (KaTeX):** Render all formulas and step-by-step derivations in KaTeX ($...$ or $$...$$).
"""
