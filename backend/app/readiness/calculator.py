import math
import statistics
from typing import Any, Dict, List, Optional, Tuple

from backend.app.readiness.schemas import (
    HighRoiTopicRecommendation,
    ReadinessComponentBreakdown,
    TopicReadinessDetail,
)


class ReadinessScoreCalculator:
    """
    Pure mathematical calculation engine for psychometric multi-factor fusion,
    Ebbinghaus memory decay, logistic pass probability, and marginal ROI knapsack prioritization.
    """

    @classmethod
    def calculate_topic_mastery_component(cls, topics: List[Dict[str, Any]]) -> float:
        """
        Computes the blueprint-weighted BKT topic mastery score (0-100%).
        Formula: W_m = 100 * sum(w_i * L_i) / sum(w_i)
        """
        if not topics:
            return 0.0

        total_weight = sum(t.get("target_weight", 1.0) for t in topics)
        if total_weight <= 0:
            total_weight = float(len(topics))
            for t in topics:
                t["target_weight"] = 1.0

        weighted_sum = sum(
            (t.get("target_weight", 1.0) * max(0.0, min(1.0, t.get("p_mastery", 0.1))))
            for t in topics
        )

        return round((weighted_sum / total_weight) * 100.0, 2)

    @classmethod
    def calculate_retention_component(cls, topics: List[Dict[str, Any]]) -> float:
        """
        Computes the blueprint-weighted continuous Ebbinghaus memory retrievability score (0-100%).
        Formula: W_r = 100 * sum(w_i * R_i) / sum(w_i)
        """
        if not topics:
            return 0.0

        total_weight = sum(t.get("target_weight", 1.0) for t in topics)
        if total_weight <= 0:
            total_weight = float(len(topics))

        weighted_sum = sum(
            (t.get("target_weight", 1.0) * max(0.0, min(1.0, t.get("retrievability", 1.0))))
            for t in topics
        )

        return round((weighted_sum / total_weight) * 100.0, 2)

    @classmethod
    def calculate_simulation_component(cls, mock_reports: List[Dict[str, Any]]) -> Optional[float]:
        """
        Computes recency-weighted full-length mock simulation performance (0-100%).
        Formula: W_s = sum(lambda^k * Score_k) / sum(lambda^k)
        """
        if not mock_reports:
            return None

        decay_rate = 0.85
        weighted_score_sum = 0.0
        weight_sum = 0.0

        # Reports sorted newest to oldest
        for i, report in enumerate(mock_reports):
            w = math.pow(decay_rate, i)
            score = float(report.get("percentage_score", 0.0))
            weighted_score_sum += w * score
            weight_sum += w

        if weight_sum <= 0:
            return 0.0

        return round(weighted_score_sum / weight_sum, 2)

    @classmethod
    def calculate_pacing_component(
        cls,
        latencies: List[float],
        benchmark_budget_seconds: float = 120.0,
    ) -> float:
        """
        Computes response latency consistency and pacing reliability score (0-100%).
        Formula: W_p = 100 * max(0.0, 1.0 - sigma_t / (2 * t_budget))
        """
        if not latencies or len(latencies) < 2:
            return 85.0  # Neutral prior for limited timing data

        std_dev = statistics.stdev(latencies)
        pacing_factor = max(0.0, 1.0 - (std_dev / (2.0 * max(10.0, benchmark_budget_seconds))))
        return round(pacing_factor * 100.0, 2)

    @classmethod
    def calculate_composite_readiness(
        cls,
        mastery_score: float,
        retention_score: float,
        simulation_score: Optional[float],
        pacing_score: float,
    ) -> Tuple[float, ReadinessComponentBreakdown]:
        """
        Synthesizes multi-factor telemetry into composite readiness score and component breakdown.
        """
        if simulation_score is not None:
            w_m = 0.40
            w_r = 0.20
            w_s = 0.25
            w_p = 0.15
            effective_sim_score = simulation_score
        else:
            # Rebalance weights when mock exam data is not yet available
            # 0.40/0.75 = 0.533, 0.20/0.75 = 0.267, 0.15/0.75 = 0.200
            w_m = 0.533
            w_r = 0.267
            w_s = 0.0
            w_p = 0.200
            effective_sim_score = (mastery_score + retention_score) / 2.0

        composite = (
            w_m * mastery_score
            + w_r * retention_score
            + w_s * (simulation_score if simulation_score is not None else 0.0)
            + w_p * pacing_score
        )
        clamped_score = max(0.0, min(100.0, round(composite, 2)))

        breakdown = ReadinessComponentBreakdown(
            mastery_score=round(mastery_score, 2),
            mastery_weight=w_m,
            retention_score=round(retention_score, 2),
            retention_weight=w_r,
            simulation_score=round(effective_sim_score, 2),
            simulation_weight=w_s,
            pacing_score=round(pacing_score, 2),
            pacing_weight=w_p,
        )

        return clamped_score, breakdown

    @classmethod
    def calculate_pass_probability(
        cls,
        readiness_score: float,
        passing_threshold: float = 60.0,
        k: float = 0.10,
    ) -> float:
        """
        Calculates calibrated sigmoid probability of scoring >= passing_threshold on exam day.
        Formula: P(Pass) = 1 / (1 + exp(-k * (S - theta)))
        """
        exponent = -k * (readiness_score - passing_threshold)
        # Guard against overflow
        exponent = max(-50.0, min(50.0, exponent))
        prob = 1.0 / (1.0 + math.exp(exponent))
        return round(prob, 4)

    @classmethod
    def classify_readiness_tier(cls, readiness_score: float) -> str:
        if readiness_score >= 80.0:
            return "High Readiness"
        elif readiness_score >= 60.0:
            return "Moderate Readiness"
        else:
            return "Needs Remediation"

    @classmethod
    def rank_high_roi_topics(
        cls,
        topics: List[Dict[str, Any]],
        top_n: int = 3,
    ) -> List[HighRoiTopicRecommendation]:
        """
        Computes marginal score gain per hour of study and ranks top high-ROI focus areas.
        """
        recommendations: List[Tuple[float, HighRoiTopicRecommendation]] = []

        total_w = sum(t.get("target_weight", 1.0) for t in topics) or 1.0

        for t in topics:
            norm_w = t.get("target_weight", 1.0) / total_w
            m_level = max(0.0, min(1.0, t.get("p_mastery", 0.1)))
            r_level = max(0.0, min(1.0, t.get("retrievability", 1.0)))

            # Effective current strength is limited by both mastery and memory retention
            effective_competence = min(m_level, r_level)
            competence_deficit = 1.0 - effective_competence

            # Potential point gain on exam = weight * deficit * 100
            potential_gain = round(norm_w * competence_deficit * 100.0, 1)

            est_hours = max(1.0, float(t.get("estimated_hours", 2.0)))
            roi = potential_gain / est_hours

            weight_pct = round(norm_w * 100.0, 1)
            mastery_pct = round(m_level * 100.0, 1)
            retention_pct = round(r_level * 100.0, 1)

            reason_parts = []
            if norm_w >= 0.15:
                reason_parts.append(f"High blueprint weighting ({weight_pct}%)")
            if m_level < 0.50:
                reason_parts.append(f"low mastery ({mastery_pct}%)")
            elif r_level < 0.60:
                reason_parts.append(f"memory decay ({retention_pct}% retention)")

            reason = f"{', '.join(reason_parts) if reason_parts else 'Improvement gap'} yields +{potential_gain} potential exam points."

            rec = HighRoiTopicRecommendation(
                topic_id=t["topic_id"],
                topic_title=t["topic_title"],
                target_weight=weight_pct,
                current_mastery_pct=mastery_pct,
                current_retention_pct=retention_pct,
                potential_score_gain=potential_gain,
                reason=reason,
            )
            recommendations.append((roi, rec))

        # Sort descending by marginal ROI
        recommendations.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in recommendations[:top_n]]
