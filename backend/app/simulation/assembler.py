from datetime import datetime, timezone
import logging
import random
from typing import List, Set
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import Subject, Topic
from backend.app.questions.models import Question, ValidationStatus
from backend.app.simulation.models import BlueprintTopicDistribution, ExamBlueprint

logger = logging.getLogger("adaptive_exam_platform.simulation.assembler")


class StratifiedBlueprintAssembler:
    """
    Assembles balanced mock exam papers by stratifying question selection across syllabus topics
    according to Exam Blueprint distributions (PRD Cap 14, FR-014).
    """

    @classmethod
    async def assemble_paper(
        cls,
        session: AsyncSession,
        blueprint: ExamBlueprint,
    ) -> List[Question]:
        # 1. Fetch Topic Distributions for this blueprint
        dist_stmt = select(BlueprintTopicDistribution).where(
            BlueprintTopicDistribution.blueprint_id == blueprint.id
        )
        distributions = (await session.exec(dist_stmt)).all()

        selected_questions: List[Question] = []
        selected_ids: Set[str] = set()

        # 2. Sample questions per topic distribution
        if distributions:
            for dist in distributions:
                quota = dist.target_question_count
                if quota <= 0:
                    continue

                # Query validated questions for this specific topic
                q_stmt = select(Question).where(
                    Question.topic_id == dist.topic_id,
                    Question.validation_status == ValidationStatus.VALIDATED,
                )
                candidates = (await session.exec(q_stmt)).all()

                # Fallback to any questions for this topic if validated pool is small
                if not candidates:
                    fallback_stmt = select(Question).where(Question.topic_id == dist.topic_id)
                    candidates = (await session.exec(fallback_stmt)).all()

                # Filter out already selected
                available = [q for q in candidates if q.id not in selected_ids]
                sample_count = min(len(available), quota)
                
                if sample_count > 0:
                    picked = random.sample(available, sample_count)
                    for p in picked:
                        selected_questions.append(p)
                        selected_ids.add(p.id)

        # 3. Fill remaining deficit if blueprint question count is not met
        deficit = blueprint.total_questions - len(selected_questions)
        if deficit > 0:
            # Query all subjects/topics under this exam template
            topic_stmt = select(Topic).join(Subject).where(Subject.exam_template_id == blueprint.exam_template_id)
            exam_topics = (await session.exec(topic_stmt)).all()
            exam_topic_ids = [t.id for t in exam_topics]

            if exam_topic_ids:
                remaining_stmt = select(Question).where(
                    Question.topic_id.in_(exam_topic_ids),
                    Question.validation_status == ValidationStatus.VALIDATED,
                )
                remaining_candidates = (await session.exec(remaining_stmt)).all()
                if not remaining_candidates:
                    remaining_stmt = select(Question).where(Question.topic_id.in_(exam_topic_ids))
                    remaining_candidates = (await session.exec(remaining_stmt)).all()

                available_remaining = [q for q in remaining_candidates if q.id not in selected_ids]
                fill_count = min(len(available_remaining), deficit)
                if fill_count > 0:
                    picked = random.sample(available_remaining, fill_count)
                    for p in picked:
                        selected_questions.append(p)
                        selected_ids.add(p.id)

        # 4. Sort questions logically by topic order
        if selected_questions:
            topic_ids = list({q.topic_id for q in selected_questions})
            topics_db = (await session.exec(select(Topic).where(Topic.id.in_(topic_ids)))).all()
            topic_order_map = {t.id: t.order for t in topics_db}

            def _sort_key(q: Question):
                topic_ord = topic_order_map.get(q.topic_id, 999)
                created = q.created_at
                if created is None:
                    return (topic_ord, 0)
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                return (topic_ord, created.timestamp())

            selected_questions.sort(key=_sort_key)

        logger.info(
            f"Assembled stratified paper for blueprint '{blueprint.code}': "
            f"{len(selected_questions)}/{blueprint.total_questions} questions across {len(distributions)} distributions."
        )

        return selected_questions
