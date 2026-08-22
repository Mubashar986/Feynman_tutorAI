import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import BloomLevel, ExamBoard, TopicDifficulty
from backend.app.curriculum.schemas import (
    ExamTemplateImportSchema,
    SubjectImportSchema,
    TopicImportSchema,
    LearningObjectiveImportSchema,
    TopicPrerequisiteImportSchema,
)
from backend.app.curriculum.service import (
    CurriculumService,
    SyllabusParserService,
    HAS_YAML,
)



# Sample valid nested blueprint dictionary
SAMPLE_PHYSICS_BLUEPRINT = {
    "title": "Cambridge International A-Level Physics",
    "code": "9702-TEST",
    "board": "Cambridge International",
    "description": "Comprehensive syllabus for Cambridge A-Level Physics.",
    "difficulty_level": "Advanced Placement / A-Level",
    "icon_name": "Atom",
    "total_duration_minutes": 120,
    "passing_score_percentage": 75.0,
    "subjects": [
        {
            "title": "General Physics & Mechanics",
            "order": 1,
            "description": "Foundations of classical mechanics and measurements.",
            "topics": [
                {
                    "title": "Physical Quantities & Units",
                    "code": "TOPIC-PHY-01",
                    "order": 1,
                    "difficulty": "foundational",
                    "estimated_hours": 3.0,
                    "importance_weight": 1.0,
                    "description": "SI units and dimensional analysis.",
                    "objectives": [
                        {
                            "code": "9702.1.1",
                            "description": "Understand and use SI base units.",
                            "bloom_level": "Understand",
                        }
                    ],
                    "subtopics": [
                        {"title": "Base Units", "order": 1, "description": "kg, m, s, A, K, mol"}
                    ],
                    "prerequisites": [],
                },
                {
                    "title": "Kinematics & Dynamics",
                    "code": "TOPIC-PHY-02",
                    "order": 2,
                    "difficulty": "intermediate",
                    "estimated_hours": 6.0,
                    "importance_weight": 1.5,
                    "description": "Motion in 1D and 2D with Newton's laws.",
                    "objectives": [
                        {
                            "code": "9702.2.1",
                            "description": "Derive projectile range formula.",
                            "formula_latex": "R = \\frac{u^2 \\sin(2\\theta)}{g}",
                            "bloom_level": "Apply",
                        }
                    ],
                    "subtopics": [],
                    "prerequisites": [
                        {
                            "prerequisite_topic_code_or_title": "TOPIC-PHY-01",
                            "is_mandatory": True,
                        }
                    ],
                },
            ],
        }
    ],
}


# ==============================================================================
# 1. Blueprint Parsing Unit Tests
# ==============================================================================

def test_parse_valid_json_blueprint():
    import json
    raw_json = json.dumps(SAMPLE_PHYSICS_BLUEPRINT)
    schema = SyllabusParserService.parse_yaml_or_json(raw_json)
    assert schema.code == "9702-TEST"
    assert len(schema.subjects) == 1
    assert len(schema.subjects[0].topics) == 2


@pytest.mark.skipif(not HAS_YAML, reason="pyyaml is optional")
def test_parse_valid_yaml_blueprint():
    raw_yaml = """
title: "AP Calculus BC"
code: "AP-CALC-BC-TEST"
board: "College Board"
description: "College Board AP Calculus BC blueprint."
difficulty_level: "Advanced Placement / A-Level"
icon_name: "Sigma"
total_duration_minutes: 195
passing_score_percentage: 65.0
subjects:
  - title: "Differential Calculus"
    order: 1
    description: "Limits and derivatives"
    topics:
      - title: "Limits and Continuity"
        code: "CALC-01"
        order: 1
        difficulty: "foundational"
        estimated_hours: 4.0
        importance_weight: 1.2
        description: "Evaluating limits"
        objectives:
          - code: "CALC.1.1"
            description: "Calculate limits algebraically."
            bloom_level: "Apply"
"""
    schema = SyllabusParserService.parse_yaml_or_json(raw_yaml)
    assert schema.code == "AP-CALC-BC-TEST"
    assert schema.board == ExamBoard.COLLEGE_BOARD
    assert len(schema.subjects) == 1
    assert schema.subjects[0].topics[0].objectives[0].bloom_level == BloomLevel.APPLY


def test_parse_malformed_blueprint_raises_422():
    with pytest.raises(Exception) as exc_info:
        SyllabusParserService.parse_yaml_or_json("invalid: [yaml: string: {{")
    assert "422" in str(exc_info.value) or "validation failed" in str(exc_info.value).lower()


import uuid

def get_sample_blueprint(code_suffix: str = "") -> dict:
    bp = dict(SAMPLE_PHYSICS_BLUEPRINT)
    code = f"9702-TEST-{code_suffix}" if code_suffix else f"9702-TEST-{uuid.uuid4().hex[:6]}"
    bp["code"] = code
    return bp


# ==============================================================================
# 2. Relational Database Service Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_import_blueprint_creates_nested_entities(db_session: AsyncSession):
    bp = get_sample_blueprint("NESTED")
    schema = ExamTemplateImportSchema.model_validate(bp)
    template = await SyllabusParserService.import_blueprint(db_session, schema)

    assert template.id is not None
    assert template.code == "9702-TEST-NESTED"

    # Verify syllabus tree query
    syllabus = await CurriculumService.get_syllabus_tree(db_session, template.id)
    assert len(syllabus) == 1
    subject = syllabus[0]
    assert subject.title == "General Physics & Mechanics"
    assert len(subject.topics) == 2

    # Verify topics, objectives, and prerequisites
    topic1 = subject.topics[0]
    assert topic1.title == "Physical Quantities & Units"
    assert len(topic1.objectives) == 1
    assert topic1.objectives[0].code == "9702.1.1"

    topic2 = subject.topics[1]
    assert topic2.title == "Kinematics & Dynamics"
    assert len(topic2.prerequisites) == 1
    assert topic2.prerequisites[0].prerequisite_topic_id == topic1.id
    assert topic2.prerequisites[0].prerequisite_topic_title == "Physical Quantities & Units"


@pytest.mark.asyncio
async def test_import_duplicate_code_raises_conflict(db_session: AsyncSession):
    bp = get_sample_blueprint("DUP")
    schema = ExamTemplateImportSchema.model_validate(bp)
    # First import succeeds
    await SyllabusParserService.import_blueprint(db_session, schema)

    # Second import with identical code must fail
    with pytest.raises(Exception) as exc_info:
        await SyllabusParserService.import_blueprint(db_session, schema)
    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_exam_templates_aggregates_counts(db_session: AsyncSession):
    bp = get_sample_blueprint("COUNTS")
    schema = ExamTemplateImportSchema.model_validate(bp)
    await SyllabusParserService.import_blueprint(db_session, schema)

    templates = await CurriculumService.list_exam_templates(db_session)
    assert len(templates) >= 1
    target = next(t for t in templates if t.code == "9702-TEST-COUNTS")
    assert target.subject_count == 1
    assert target.topic_count == 2
    assert target.objective_count == 2


@pytest.mark.asyncio
async def test_delete_exam_template_cascades(db_session: AsyncSession):
    bp = get_sample_blueprint("DELETE")
    schema = ExamTemplateImportSchema.model_validate(bp)
    template = await SyllabusParserService.import_blueprint(db_session, schema)

    # Delete template
    deleted = await CurriculumService.delete_exam_template(db_session, template.id)
    assert deleted is True

    # Verify template is gone
    res = await CurriculumService.get_exam_template(db_session, template.id)
    assert res is None



# ==============================================================================
# 3. FastAPI Endpoint Integration & Role Protection Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_catalog_endpoints_accessible_without_auth(async_client: AsyncClient):
    # Public catalog endpoint
    resp = await async_client.get("/api/v1/exam-templates")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_import_blueprint_role_protection(async_client: AsyncClient):
    # 1. Student attempts import -> MUST BE 403 FORBIDDEN
    student_email = "curriculum.student@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": student_email, "password": "Password123!", "full_name": "Student A", "role": "student"},
    )
    login_student = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student_email, "password": "Password123!"},
    )
    student_token = login_student.json()["access_token"]

    resp = await async_client.post(
        "/api/v1/exam-templates/import",
        json=SAMPLE_PHYSICS_BLUEPRINT,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 403
    assert "Access forbidden" in resp.json()["detail"]

    # 2. Instructor attempts import -> MUST BE 201 CREATED
    instructor_email = "curriculum.instructor@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": instructor_email, "password": "Password123!", "full_name": "Dr. Smith", "role": "instructor"},
    )
    login_inst = await async_client.post(
        "/api/v1/auth/login",
        json={"email": instructor_email, "password": "Password123!"},
    )
    inst_token = login_inst.json()["access_token"]

    blueprint_copy = dict(SAMPLE_PHYSICS_BLUEPRINT)
    blueprint_copy["code"] = "9702-API-TEST"
    import_resp = await async_client.post(
        "/api/v1/exam-templates/import",
        json=blueprint_copy,
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert import_resp.status_code == 201
    created_exam = import_resp.json()
    assert created_exam["code"] == "9702-API-TEST"

    # 3. Query the imported syllabus tree via public GET endpoint
    tree_resp = await async_client.get(f"/api/v1/exam-templates/{created_exam['id']}/syllabus")
    assert tree_resp.status_code == 200
    subjects = tree_resp.json()
    assert len(subjects) == 1
    assert len(subjects[0]["topics"]) == 2

    # 4. Query topic detail
    topic_id = subjects[0]["topics"][1]["id"]
    topic_resp = await async_client.get(f"/api/v1/exam-templates/topics/{topic_id}")
    assert topic_resp.status_code == 200
    topic_detail = topic_resp.json()
    assert topic_detail["title"] == "Kinematics & Dynamics"
    assert len(topic_detail["objectives"]) == 1
    assert "sin(2" in topic_detail["objectives"][0]["formula_latex"]
