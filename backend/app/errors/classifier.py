import re
from typing import Optional, Tuple
from backend.app.errors.models import ErrorCategory


class ErrorDiagnosticClassifier:
    """
    Cognitive diagnostic taxonomy classifier (PRD §12, FR-006, FR-012).
    Maps distractor rationales and question options to structured ErrorCategories and Misconception metadata.
    """

    CALCULATION_KEYWORDS = [
        "arithmetic", "computational", "calculation", "multiplied", "divided", "subtracted",
        "added", "factor of", "algebraic", "inverted ratio", "sign error", "decimal",
        "forgot the factor", "multiplied instead", "divided instead",
    ]

    MISREAD_KEYWORDS = [
        "misread", "unit", "conversion", "overlooked", "not", "except", "confused with",
        "radius instead of diameter", "minutes instead of seconds", "km/h",
    ]

    INCOMPLETE_KEYWORDS = [
        "incomplete", "intermediate", "premature", "early stop", "forgot to square root",
        "forgot to integrate", "partial derivation",
    ]

    REPRESENTATIONAL_KEYWORDS = [
        "graph", "slope", "area under", "coordinate", "vector", "direction", "diagram",
        "free body", "axis", "perpendicular",
    ]

    @classmethod
    def classify_error(
        cls,
        distractor_rationale: Optional[str] = None,
        question_prompt: Optional[str] = None,
        topic_title: Optional[str] = None,
    ) -> Tuple[ErrorCategory, str, str, str]:
        """
        Classifies student error into an ErrorCategory and extracts misconception metadata.
        Returns: (category, code, title, description)
        """
        rationale = (distractor_rationale or "").strip().lower()
        topic_clean = (topic_title or "general").strip().lower()

        # 1. Determine ErrorCategory
        category = ErrorCategory.CONCEPTUAL  # Default

        if any(kw in rationale for kw in cls.CALCULATION_KEYWORDS):
            category = ErrorCategory.CALCULATION
        elif any(kw in rationale for kw in cls.MISREAD_KEYWORDS):
            category = ErrorCategory.MISREAD
        elif any(kw in rationale for kw in cls.INCOMPLETE_KEYWORDS):
            category = ErrorCategory.INCOMPLETE
        elif any(kw in rationale for kw in cls.REPRESENTATIONAL_KEYWORDS):
            category = ErrorCategory.REPRESENTATIONAL

        # 2. Generate Misconception Code & Title
        if distractor_rationale and len(distractor_rationale.strip()) > 3:
            raw_title = distractor_rationale.strip()
            if len(raw_title) > 80:
                raw_title = raw_title[:77] + "..."
            title = raw_title
            description = distractor_rationale.strip()
            # Slug generation
            slug = re.sub(r"[^a-zA-Z0-9]+", "_", distractor_rationale[:30].strip()).upper()
            code = f"MISC_{slug.strip('_')}"
        else:
            title = f"Conceptual misunderstanding in {topic_clean.title()}"
            description = f"Incorrect response indicating unaddressed cognitive gap in {topic_clean}."
            code = f"MISC_{re.sub(r'[^a-zA-Z0-9]+', '_', topic_clean).upper()}_DEFAULT"

        remediation_guidance = (
            f"Review the fundamental principles of {topic_clean}. "
            f"Address the diagnostic error pattern: {title}."
        )

        return category, code, title, description, remediation_guidance
