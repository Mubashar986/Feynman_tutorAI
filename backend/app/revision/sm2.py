import math
from typing import Tuple
from backend.app.revision.models import CardState, ReviewRating


class SM2Engine:
    """
    Pure mathematical implementation of SuperMemo-2 (SM-2) & Memory Retrievability (PRD FR-007, Cap 7).
    """

    MIN_EASE_FACTOR: float = 1.30
    MAX_EASE_FACTOR: float = 2.80
    DEFAULT_EASE_FACTOR: float = 2.50

    @classmethod
    def calculate_next_interval(
        cls,
        repetitions: int,
        interval_days: float,
        ease_factor: float,
        rating: ReviewRating,
    ) -> Tuple[int, float, float, CardState, float]:
        """
        Calculates the next repetition count, interval (in days), ease factor, card state, and estimated stability.

        Returns:
            (new_repetitions, new_interval_days, new_ease_factor, new_card_state, new_stability)
        """
        ef = max(cls.MIN_EASE_FACTOR, min(cls.MAX_EASE_FACTOR, ease_factor))

        if rating == ReviewRating.AGAIN:
            # Memory lapse / failed recall
            new_repetitions = 0
            new_interval = 1.0
            new_ef = max(cls.MIN_EASE_FACTOR, ef - 0.20)
            new_state = CardState.RELEARNING
            new_stability = 1.0

        elif rating == ReviewRating.HARD:
            # Recalled with difficulty
            new_repetitions = repetitions + 1
            if repetitions == 0:
                new_interval = 1.0
            elif repetitions == 1:
                new_interval = 3.0
            else:
                new_interval = max(1.0, round(interval_days * 1.2, 1))

            new_ef = max(cls.MIN_EASE_FACTOR, ef - 0.15)
            new_state = CardState.REVIEW if new_repetitions >= 2 else CardState.LEARNING
            new_stability = new_interval

        elif rating == ReviewRating.GOOD:
            # Standard successful recall
            new_repetitions = repetitions + 1
            if repetitions == 0:
                new_interval = 1.0
            elif repetitions == 1:
                new_interval = 6.0
            else:
                new_interval = max(1.0, round(interval_days * ef, 1))

            new_ef = ef
            new_state = CardState.REVIEW if new_repetitions >= 2 else CardState.LEARNING
            new_stability = new_interval

        else:  # ReviewRating.EASY
            # Effortless rapid recall
            new_repetitions = repetitions + 1
            if repetitions == 0:
                new_interval = 3.0
            elif repetitions == 1:
                new_interval = 8.0
            else:
                new_interval = max(1.0, round(interval_days * ef * 1.3, 1))

            new_ef = min(cls.MAX_EASE_FACTOR, ef + 0.15)
            new_state = CardState.REVIEW
            new_stability = new_interval

        return (
            new_repetitions,
            round(new_interval, 1),
            round(new_ef, 2),
            new_state,
            round(new_stability, 1),
        )

    @classmethod
    def calculate_retrievability(cls, days_elapsed: float, stability: float) -> float:
        """
        Calculates Ebbinghaus memory retrievability: R(t) = exp(-t / S).
        Returns a float probability in [0.0, 1.0].
        """
        if stability <= 0.0 or days_elapsed <= 0.0:
            return 1.0
        r = math.exp(-days_elapsed / stability)
        return max(0.0, min(1.0, round(r, 4)))
