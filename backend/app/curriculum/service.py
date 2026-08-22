import json
from typing import Any, Dict, List, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    yaml = None
    HAS_YAML = False

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import (
    ExamTemplate,
    Subject,
    Section,
    Topic,
    Subtopic,
    LearningObjective,
    TopicPrerequisite,
)
from backend.app.curriculum.schemas import (
    ExamTemplateImportSchema,
    ExamTemplateResponse,
    ExamTemplateDetailResponse,
    SubjectDetailResponse,
    TopicDetailResponse,
    SubtopicResponse,
    LearningObjectiveResponse,
    TopicPrerequisiteResponse,
)


class CurriculumService:
    """
    Domain service for querying and managing exam templates and syllabus hierarchies.
    """

    @staticmethod
    async def list_exam_templates(session: AsyncSession) -> List[ExamTemplateResponse]:
        """
        Lists all active exam templates with aggregate counts.
        """
        statement = select(ExamTemplate).where(ExamTemplate.is_active == True).order_by(ExamTemplate.title)
        result = await session.execute(statement)
        templates = result.scalars().all()

        responses = []
        for t in templates:
            # Count subjects
            subj_stmt = select(Subject).where(Subject.exam_template_id == t.id)
            subj_res = await session.execute(subj_stmt)
            subjects = subj_res.scalars().all()
            subject_ids = [s.id for s in subjects]

            # Count topics
            topic_count = 0
            objective_count = 0
            if subject_ids:
                topic_stmt = select(Topic).where(Topic.subject_id.in_(subject_ids))
                topic_res = await session.execute(topic_stmt)
                topics = topic_res.scalars().all()
                topic_count = len(topics)
                topic_ids = [top.id for top in topics]

                if topic_ids:
                    obj_stmt = select(LearningObjective).where(LearningObjective.topic_id.in_(topic_ids))
                    obj_res = await session.execute(obj_stmt)
                    objective_count = len(obj_res.scalars().all())

            resp = ExamTemplateResponse(
                id=t.id,
                title=t.title,
                code=t.code,
                board=t.board,
                description=t.description,
                difficulty_level=t.difficulty_level,
                icon_name=t.icon_name,
                total_duration_minutes=t.total_duration_minutes,
                passing_score_percentage=t.passing_score_percentage,
                is_active=t.is_active,
                subject_count=len(subjects),
                topic_count=topic_count,
                objective_count=objective_count,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            responses.append(resp)

        return responses

    @staticmethod
    async def get_exam_template(session: AsyncSession, template_id: str) -> Optional[ExamTemplate]:
        """
        Fetches an exam template by ID or code.
        """
        stmt = select(ExamTemplate).where(
            (ExamTemplate.id == template_id) | (ExamTemplate.code == template_id)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_syllabus_tree(session: AsyncSession, template_id: str) -> List[SubjectDetailResponse]:
        """
        Fetches the complete nested syllabus tree for an exam template.
        """
        template = await CurriculumService.get_exam_template(session, template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exam template '{template_id}' not found",
            )

        subj_stmt = select(Subject).where(Subject.exam_template_id == template.id).order_by(Subject.order)
        subj_res = await session.execute(subj_stmt)
        subjects = subj_res.scalars().all()

        subject_details = []
        for s in subjects:
            top_stmt = select(Topic).where(Topic.subject_id == s.id).order_by(Topic.order)
            top_res = await session.execute(top_stmt)
            topics = top_res.scalars().all()

            topic_details = []
            for top in topics:
                # Objectives
                obj_stmt = select(LearningObjective).where(LearningObjective.topic_id == top.id).order_by(LearningObjective.code)
                obj_res = await session.execute(obj_stmt)
                objectives = [LearningObjectiveResponse.model_validate(o) for o in obj_res.scalars().all()]

                # Subtopics
                sub_stmt = select(Subtopic).where(Subtopic.topic_id == top.id).order_by(Subtopic.order)
                sub_res = await session.execute(sub_stmt)
                subtopics = [SubtopicResponse.model_validate(sub) for sub in sub_res.scalars().all()]

                # Prerequisites
                prereq_stmt = select(TopicPrerequisite).where(TopicPrerequisite.topic_id == top.id)
                prereq_res = await session.execute(prereq_stmt)
                prereqs = []
                for p in prereq_res.scalars().all():
                    # Get title of prerequisite topic
                    p_top_stmt = select(Topic).where(Topic.id == p.prerequisite_topic_id)
                    p_top_res = await session.execute(p_top_stmt)
                    p_top = p_top_res.scalar_one_or_none()
                    prereqs.append(
                        TopicPrerequisiteResponse(
                            id=p.id,
                            topic_id=p.topic_id,
                            prerequisite_topic_id=p.prerequisite_topic_id,
                            prerequisite_topic_title=p_top.title if p_top else "Unknown Prerequisite",
                            is_mandatory=p.is_mandatory,
                        )
                    )

                topic_details.append(
                    TopicDetailResponse(
                        id=top.id,
                        subject_id=top.subject_id,
                        section_id=top.section_id,
                        title=top.title,
                        order=top.order,
                        difficulty=top.difficulty,
                        estimated_hours=top.estimated_hours,
                        importance_weight=top.importance_weight,
                        description=top.description,
                        subtopics=subtopics,
                        objectives=objectives,
                        prerequisites=prereqs,
                        created_at=top.created_at,
                        updated_at=top.updated_at,
                    )
                )

            subject_details.append(
                SubjectDetailResponse(
                    id=s.id,
                    exam_template_id=s.exam_template_id,
                    title=s.title,
                    order=s.order,
                    description=s.description,
                    topics=topic_details,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )

        return subject_details

    @staticmethod
    async def get_topic_detail(session: AsyncSession, topic_id: str) -> Optional[TopicDetailResponse]:
        """
        Fetches detailed information, objectives, and prerequisites for a single topic.
        """
        stmt = select(Topic).where(Topic.id == topic_id)
        res = await session.execute(stmt)
        top = res.scalar_one_or_none()
        if not top:
            return None

        # Objectives
        obj_stmt = select(LearningObjective).where(LearningObjective.topic_id == top.id).order_by(LearningObjective.code)
        obj_res = await session.execute(obj_stmt)
        objectives = [LearningObjectiveResponse.model_validate(o) for o in obj_res.scalars().all()]

        # Subtopics
        sub_stmt = select(Subtopic).where(Subtopic.topic_id == top.id).order_by(Subtopic.order)
        sub_res = await session.execute(sub_stmt)
        subtopics = [SubtopicResponse.model_validate(sub) for sub in sub_res.scalars().all()]

        # Prerequisites
        prereq_stmt = select(TopicPrerequisite).where(TopicPrerequisite.topic_id == top.id)
        prereq_res = await session.execute(prereq_stmt)
        prereqs = []
        for p in prereq_res.scalars().all():
            p_top_stmt = select(Topic).where(Topic.id == p.prerequisite_topic_id)
            p_top_res = await session.execute(p_top_stmt)
            p_top = p_top_res.scalar_one_or_none()
            prereqs.append(
                TopicPrerequisiteResponse(
                    id=p.id,
                    topic_id=p.topic_id,
                    prerequisite_topic_id=p.prerequisite_topic_id,
                    prerequisite_topic_title=p_top.title if p_top else "Unknown Prerequisite",
                    is_mandatory=p.is_mandatory,
                )
            )

        return TopicDetailResponse(
            id=top.id,
            subject_id=top.subject_id,
            section_id=top.section_id,
            title=top.title,
            order=top.order,
            difficulty=top.difficulty,
            estimated_hours=top.estimated_hours,
            importance_weight=top.importance_weight,
            description=top.description,
            subtopics=subtopics,
            objectives=objectives,
            prerequisites=prereqs,
            created_at=top.created_at,
            updated_at=top.updated_at,
        )

    @staticmethod
    async def delete_exam_template(session: AsyncSession, template_id: str) -> bool:
        """
        Deletes an exam template and cascades to subjects, topics, objectives.
        """
        template = await CurriculumService.get_exam_template(session, template_id)
        if not template:
            return False

        # Fetch subjects
        subj_stmt = select(Subject).where(Subject.exam_template_id == template.id)
        subj_res = await session.execute(subj_stmt)
        subjects = subj_res.scalars().all()
        subj_ids = [s.id for s in subjects]

        if subj_ids:
            # Fetch topics
            top_stmt = select(Topic).where(Topic.subject_id.in_(subj_ids))
            top_res = await session.execute(top_stmt)
            topics = top_res.scalars().all()
            top_ids = [t.id for t in topics]

            if top_ids:
                # Delete prerequisites
                prereq_stmt = select(TopicPrerequisite).where(
                    (TopicPrerequisite.topic_id.in_(top_ids)) | (TopicPrerequisite.prerequisite_topic_id.in_(top_ids))
                )
                prereq_res = await session.execute(prereq_stmt)
                for p in prereq_res.scalars().all():
                    await session.delete(p)

                # Delete objectives
                obj_stmt = select(LearningObjective).where(LearningObjective.topic_id.in_(top_ids))
                obj_res = await session.execute(obj_stmt)
                for o in obj_res.scalars().all():
                    await session.delete(o)

                # Delete subtopics
                sub_stmt = select(Subtopic).where(Subtopic.topic_id.in_(top_ids))
                sub_res = await session.execute(sub_stmt)
                for sub in sub_res.scalars().all():
                    await session.delete(sub)

                for t in topics:
                    await session.delete(t)

            for s in subjects:
                await session.delete(s)

        await session.delete(template)
        await session.flush()
        return True


class SyllabusParserService:
    """
    Ingestion service that parses structured JSON/YAML curriculum blueprints into relational models.
    """

    @staticmethod
    def parse_yaml_or_json(raw_content: str) -> ExamTemplateImportSchema:
        """
        Parses a raw text string (JSON or YAML) into an ExamTemplateImportSchema.
        """
        data = None
        try:
            # Try JSON first (native standard library)
            data = json.loads(raw_content)
        except Exception as json_err:
            if HAS_YAML and yaml is not None:
                try:
                    data = yaml.safe_load(raw_content)
                except Exception as yaml_err:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Failed to parse syllabus blueprint as JSON or YAML: {str(yaml_err)}",
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to parse syllabus blueprint as JSON: {str(json_err)} (Note: YAML parsing requires pyyaml).",
                )

        if not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Syllabus blueprint must be a JSON/YAML object/dictionary.",
            )


        try:
            return ExamTemplateImportSchema.model_validate(data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Syllabus blueprint validation failed: {str(e)}",
            )

    @classmethod
    async def import_blueprint(
        cls,
        session: AsyncSession,
        blueprint: ExamTemplateImportSchema,
    ) -> ExamTemplate:
        """
        Imports a complete nested curriculum blueprint into relational SQLModel tables within an atomic transaction.
        """
        # Check if template with same code already exists
        existing = await CurriculumService.get_exam_template(session, blueprint.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Exam template with code '{blueprint.code}' already exists.",
            )

        # 1. Create ExamTemplate
        template = ExamTemplate(
            title=blueprint.title,
            code=blueprint.code,
            board=blueprint.board,
            description=blueprint.description,
            difficulty_level=blueprint.difficulty_level,
            icon_name=blueprint.icon_name,
            total_duration_minutes=blueprint.total_duration_minutes,
            passing_score_percentage=blueprint.passing_score_percentage,
        )
        session.add(template)
        await session.flush()

        # Symbol tables for prerequisite mapping
        topic_symbol_table: Dict[str, Topic] = {}  # code_or_title -> Topic entity
        pending_prerequisites: List[Tuple[Topic, str, bool]] = []  # (Topic, prereq_key, is_mandatory)

        # 2. Iterate Subjects
        for s_idx, s_data in enumerate(blueprint.subjects):
            subject = Subject(
                exam_template_id=template.id,
                title=s_data.title,
                order=s_data.order if s_data.order else s_idx,
                description=s_data.description,
            )
            session.add(subject)
            await session.flush()

            # 3. Iterate Topics
            for t_idx, t_data in enumerate(s_data.topics):
                topic = Topic(
                    subject_id=subject.id,
                    title=t_data.title,
                    order=t_data.order if t_data.order else t_idx,
                    difficulty=t_data.difficulty,
                    estimated_hours=t_data.estimated_hours,
                    importance_weight=t_data.importance_weight,
                    description=t_data.description,
                )
                session.add(topic)
                await session.flush()

                # Register symbol table for prerequisite resolution
                topic_symbol_table[topic.title] = topic
                if t_data.code:
                    topic_symbol_table[t_data.code] = topic

                # Subtopics
                for sub_idx, sub_data in enumerate(t_data.subtopics):
                    subtopic = Subtopic(
                        topic_id=topic.id,
                        title=sub_data.title,
                        order=sub_data.order if sub_data.order else sub_idx,
                        description=sub_data.description,
                    )
                    session.add(subtopic)

                # Objectives
                for obj_data in t_data.objectives:
                    objective = LearningObjective(
                        topic_id=topic.id,
                        code=obj_data.code,
                        description=obj_data.description,
                        formula_latex=obj_data.formula_latex,
                        bloom_level=obj_data.bloom_level,
                    )
                    session.add(objective)

                # Record prerequisites to link after all topics are created
                for p_data in t_data.prerequisites:
                    pending_prerequisites.append(
                        (topic, p_data.prerequisite_topic_code_or_title, p_data.is_mandatory)
                    )

        # 4. Resolve Prerequisites
        for topic_entity, prereq_key, is_mandatory in pending_prerequisites:
            prereq_topic = topic_symbol_table.get(prereq_key)
            if prereq_topic:
                prereq_edge = TopicPrerequisite(
                    topic_id=topic_entity.id,
                    prerequisite_topic_id=prereq_topic.id,
                    is_mandatory=is_mandatory,
                )
                session.add(prereq_edge)

        await session.flush()
        return template
