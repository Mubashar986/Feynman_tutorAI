from dataclasses import dataclass
from typing import Tuple

from backend.app.mastery.models import MasteryStatus
from backend.app.questions.models import DifficultyLevel, QuestionType

EPSILON = 1e-4


@dataclass
class BKTParameters:
    """
    Bayesian Knowledge Tracing (BKT) Model Parameters (PRD FR-003, Cap 3).
    """
    p_init: float = 0.10     # Prior probability of knowing the skill P(L_0)
    p_transit: float = 0.15  # Probability of learning from attempt P(T)
    p_guess: float = 0.20    # Probability of guessing correctly without mastery P(G)
    p_slip: float = 0.10     # Probability of slipping / error despite mastery P(S)


class BKTEngine:
    """
    Pure mathematical engine implementing Bayesian Knowledge Tracing and
    1PL Item Response Theory (IRT) difficulty calibration.
    """

    @classmethod
    def _clamp(cls, val: float) -> float:
        """Clamps value to [EPSILON, 1.0 - EPSILON] to ensure strict numerical stability."""
        return max(EPSILON, min(1.0 - EPSILON, val))

    @classmethod
    def get_guess_parameter(cls, question_type: QuestionType) -> float:
        """
        Calculates question-type aware guess probability P(G).
        """
        if question_type == QuestionType.MCQ_SINGLE:
            return 0.20  # Standard 4-5 option MCQ
        elif question_type == QuestionType.MCQ_MULTI:
            return 0.10  # Multiple selection has lower random guess probability
        elif question_type in (QuestionType.NUMERICAL, QuestionType.FREE_RESPONSE, QuestionType.DERIVATION_STEP):
            return 0.05  # Open response items have minimal random guess probability
        elif question_type == QuestionType.MATCHING:
            return 0.12
        return 0.20

    @classmethod
    def compute_posterior(
        cls,
        prior_probability: float,
        is_correct: bool,
        params: BKTParameters,
    ) -> float:
        """
        Executes the 2-step Bayesian Knowledge Tracing update:
        Step 1: P(L_t | observation)
        Step 2: P(L_t) = P(L_t | observation) + (1 - P(L_t | observation)) * P(T)
        """
        p_l = cls._clamp(prior_probability)
        p_s = cls._clamp(params.p_slip)
        p_g = cls._clamp(params.p_guess)
        p_t = cls._clamp(params.p_transit)

        # Step 1: Observation Bayes Update
        if is_correct:
            numerator = p_l * (1.0 - p_s)
            denominator = (p_l * (1.0 - p_s)) + ((1.0 - p_l) * p_g)
        else:
            numerator = p_l * p_s
            denominator = (p_l * p_s) + ((1.0 - p_l) * (1.0 - p_g))

        p_obs = numerator / max(EPSILON, denominator)
        p_obs = cls._clamp(p_obs)

        # Step 2: Learning Transition Step
        p_next = p_obs + ((1.0 - p_obs) * p_t)
        return cls._clamp(p_next)

    @classmethod
    def get_mastery_status(cls, probability: float) -> MasteryStatus:
        """
        Maps continuous probability P(L_t) to discrete pedagogical status.
        """
        p = cls._clamp(probability)
        if p < 0.30:
            return MasteryStatus.NOVICE
        elif p < 0.60:
            return MasteryStatus.PRACTICING
        elif p < 0.85:
            return MasteryStatus.PROFICIENT
        else:
            return MasteryStatus.MASTERED

    @classmethod
    def get_target_difficulty(cls, probability: float) -> DifficultyLevel:
        """
        Maps live mastery probability to the optimal next item difficulty (Zone of Proximal Development).
        """
        p = cls._clamp(probability)
        if p < 0.40:
            return DifficultyLevel.EASY
        elif p < 0.70:
            return DifficultyLevel.MEDIUM
        elif p < 0.90:
            return DifficultyLevel.HARD
        else:
            return DifficultyLevel.CHALLENGE

    @classmethod
    def update_mastery(
        cls,
        prior_probability: float,
        is_correct: bool,
        question_type: QuestionType = QuestionType.MCQ_SINGLE,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        custom_params: BKTParameters = None,
    ) -> Tuple[float, MasteryStatus, DifficultyLevel]:
        """
        High-level calculation executing BKT belief update, status classification, and difficulty calibration.
        Returns: (posterior_probability, new_mastery_status, target_difficulty)
        """
        params = custom_params or BKTParameters()
        # Calibrate guess probability by question type
        params.p_guess = cls.get_guess_parameter(question_type)

        posterior = cls.compute_posterior(prior_probability, is_correct, params)
        status = cls.get_mastery_status(posterior)
        target_diff = cls.get_target_difficulty(posterior)

        return posterior, status, target_diff
