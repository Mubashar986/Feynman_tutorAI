import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.dag import TopicDAG, TopicDAGService, UnlockStatus
from backend.app.curriculum.models import TopicDifficulty
from backend.app.curriculum.schemas import ExamTemplateImportSchema
from backend.app.curriculum.service import SyllabusParserService
from backend.app.learning_state.models import LearningState
from backend.app.learning_state.service import LearningStateMachineService


# ==============================================================================
# 1. Pure Algorithmic TopicDAG Unit Tests
# ==============================================================================

def test_dag_linear_graph_topological_sort():
    dag = TopicDAG()
    dag.add_node("A", "Topic A", "S1")
    dag.add_node("B", "Topic B", "S1")
    dag.add_node("C", "Topic C", "S1")

    dag.add_edge("A", "B")  # A -> B
    dag.add_edge("B", "C")  # B -> C

    has_cycles, cycle = dag.detect_cycles()
    assert has_cycles is False
    assert cycle is None

    levels = dag.compute_node_levels()
    assert levels["A"] == 0
    assert levels["B"] == 1
    assert levels["C"] == 2

    order = [node.topic_id for node in dag.get_topological_order()]
    assert order == ["A", "B", "C"]


def test_dag_diamond_graph_levels_and_ancestors():
    dag = TopicDAG()
    dag.add_node("A", "Topic A", "S1")
    dag.add_node("B", "Topic B", "S1")
    dag.add_node("C", "Topic C", "S1")
    dag.add_node("D", "Topic D", "S1")

    # Diamond: A -> B -> D and A -> C -> D
    dag.add_edge("A", "B")
    dag.add_edge("A", "C")
    dag.add_edge("B", "D")
    dag.add_edge("C", "D")

    has_cycles, _ = dag.detect_cycles()
    assert has_cycles is False

    levels = dag.compute_node_levels()
    assert levels["A"] == 0
    assert levels["B"] == 1
    assert levels["C"] == 1
    assert levels["D"] == 2

    ancestors_d = dag.get_prerequisite_ancestors("D")
    assert ancestors_d == {"A", "B", "C"}


def test_dag_cycle_detection_two_node():
    dag = TopicDAG()
    dag.add_node("A", "Topic A", "S1")
    dag.add_node("B", "Topic B", "S1")

    dag.add_edge("A", "B")
    dag.add_edge("B", "A")  # Cycle A <-> B

    has_cycles, cycle_path = dag.detect_cycles()
    assert has_cycles is True
    assert cycle_path is not None
    assert len(cycle_path) >= 2


def test_dag_cycle_detection_three_node():
    dag = TopicDAG()
    dag.add_node("A", "Topic A", "S1")
    dag.add_node("B", "Topic B", "S1")
    dag.add_node("C", "Topic C", "S1")

    dag.add_edge("A", "B")
    dag.add_edge("B", "C")
    dag.add_edge("C", "A")  # Cycle A -> B -> C -> A

    has_cycles, cycle_path = dag.detect_cycles()
    assert has_cycles is True
    assert "A" in cycle_path and "B" in cycle_path and "C" in cycle_path


def test_dag_self_loop_detection():
    dag = TopicDAG()
    dag.add_node("A", "Topic A", "S1")
    dag.add_edge("A", "A")

    has_cycles, cycle_path = dag.detect_cycles()
    assert has_cycles is True
    assert cycle_path == ["A", "A"]


def test_dag_disconnected_components():
    dag = TopicDAG()
    dag.add_node("P1", "Physics 1", "S1")
    dag.add_node("P2", "Physics 2", "S1")
    dag.add_node("M1", "Math 1", "S2")
    dag.add_node("M2", "Math 2", "S2")

    dag.add_edge("P1", "P2")
    dag.add_edge("M1", "M2")

    has_cycles, _ = dag.detect_cycles()
    assert has_cycles is False
    assert len(dag.get_topological_order()) == 4
    assert set(dag.get_root_node_ids()) == {"P1", "M1"}
    assert set(dag.get_terminal_node_ids()) == {"P2", "M2"}


# ==============================================================================
# 2. TopicDAGService Database Integration Tests
# ==============================================================================

@pytest.fixture
def multi_topic_curriculum_blueprint():
    suffix = uuid.uuid4().hex[:6]
    return {
        "title": f"DAG Test Physics {suffix}",
        "code": f"DAG-PHY-{suffix}",
        "board": "Cambridge International",
        "description": "Multi-topic blueprint for DAG validation.",
        "difficulty_level": "Advanced Placement / A-Level",
        "icon_name": "Network",
        "total_duration_minutes": 180,
        "passing_score_percentage": 70.0,
        "subjects": [
            {
                "title": "Mechanics",
                "order": 1,
                "description": "Classical mechanics",
                "topics": [
                    {
                        "title": "SI Units",
                        "code": f"T-UNITS-{suffix}",
                        "order": 1,
                        "difficulty": "foundational",
                        "estimated_hours": 2.0,
                        "description": "Fundamental units",
                        "objectives": [{"code": f"OBJ1-{suffix}", "description": "SI units", "bloom_level": "Remember"}],
                        "prerequisites": [],
                    },
                    {
                        "title": "Vectors & Trig",
                        "code": f"T-VEC-{suffix}",
                        "order": 2,
                        "difficulty": "foundational",
                        "estimated_hours": 3.0,
                        "description": "Vector addition",
                        "objectives": [{"code": f"OBJ2-{suffix}", "description": "Vectors", "bloom_level": "Understand"}],
                        "prerequisites": [],
                    },
                    {
                        "title": "1D Kinematics",
                        "code": f"T-KIN1D-{suffix}",
                        "order": 3,
                        "difficulty": "intermediate",
                        "estimated_hours": 4.0,
                        "description": "Constant acceleration",
                        "objectives": [{"code": f"OBJ3-{suffix}", "description": "Equations of motion", "bloom_level": "Apply"}],
                        "prerequisites": [
                            {"prerequisite_topic_code_or_title": f"T-UNITS-{suffix}", "is_mandatory": True},
                            {"prerequisite_topic_code_or_title": f"T-VEC-{suffix}", "is_mandatory": True},
                        ],
                    },
                    {
                        "title": "2D Projectiles",
                        "code": f"T-PROJ2D-{suffix}",
                        "order": 4,
                        "difficulty": "advanced",
                        "estimated_hours": 5.0,
                        "description": "Projectile trajectories",
                        "objectives": [{"code": f"OBJ4-{suffix}", "description": "Trajectory math", "bloom_level": "Analyze"}],
                        "prerequisites": [
                            {"prerequisite_topic_code_or_title": f"T-KIN1D-{suffix}", "is_mandatory": True}
                        ],
                    },
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_service_get_dag_graph_and_learning_path(
    db_session: AsyncSession,
    multi_topic_curriculum_blueprint: dict,
):
    schema = ExamTemplateImportSchema.model_validate(multi_topic_curriculum_blueprint)
    template = await SyllabusParserService.import_blueprint(db_session, schema)

    # 1. Test get_dag_graph
    graph_res = await TopicDAGService.get_dag_graph(db_session, template.id)
    assert graph_res["is_acyclic"] is True
    assert graph_res["total_nodes"] == 4
    assert graph_res["total_edges"] == 3
    assert len(graph_res["root_topic_ids"]) == 2  # SI Units & Vectors
    assert len(graph_res["terminal_topic_ids"]) == 1  # 2D Projectiles

    # 2. Test get_learning_path
    path_res = await TopicDAGService.get_learning_path(db_session, template.id)
    assert path_res["total_topics"] == 4
    path_titles = [node["title"] for node in path_res["learning_path"]]
    assert path_titles[-1] == "2D Projectiles"
    assert path_titles[-2] == "1D Kinematics"


@pytest.mark.asyncio
async def test_service_student_unlock_lifecycle(
    db_session: AsyncSession,
    multi_topic_curriculum_blueprint: dict,
):
    schema = ExamTemplateImportSchema.model_validate(multi_topic_curriculum_blueprint)
    template = await SyllabusParserService.import_blueprint(db_session, schema)

    student_id = str(uuid.uuid4())

    # 1. Initial State: No topics mastered
    statuses = await TopicDAGService.get_student_unlocked_topics(db_session, template.id, student_id)
    status_map = {s["title"]: s for s in statuses}

    assert status_map["SI Units"]["unlock_status"] == UnlockStatus.UNLOCKED.value
    assert status_map["Vectors & Trig"]["unlock_status"] == UnlockStatus.UNLOCKED.value
    assert status_map["1D Kinematics"]["unlock_status"] == UnlockStatus.LOCKED.value
    assert len(status_map["1D Kinematics"]["missing_prerequisite_ids"]) == 2
    assert status_map["2D Projectiles"]["unlock_status"] == UnlockStatus.LOCKED.value

    # 2. Student masters "SI Units" only
    units_topic_id = status_map["SI Units"]["topic_id"]
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=units_topic_id,
        target_state=LearningState.CALIBRATION,
        trigger="system_init",
        actor_id=student_id,
        evidence_payload={},
    )
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=units_topic_id,
        target_state=LearningState.FOUNDATION,
        trigger="baseline_tested",
        actor_id=student_id,
        evidence_payload={},
    )
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=units_topic_id,
        target_state=LearningState.PRACTICING,
        trigger="foundation_studied",
        actor_id=student_id,
        evidence_payload={},
    )
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=units_topic_id,
        target_state=LearningState.ASSESSMENT,
        trigger="practice_completed",
        actor_id=student_id,
        evidence_payload={},
    )
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=units_topic_id,
        target_state=LearningState.MASTERY,
        trigger="assessment_passed",
        actor_id=student_id,
        evidence_payload={"score": 0.95},
    )

    statuses_after_units = await TopicDAGService.get_student_unlocked_topics(db_session, template.id, student_id)
    status_map = {s["title"]: s for s in statuses_after_units}
    assert status_map["SI Units"]["unlock_status"] == UnlockStatus.MASTERED.value
    # 1D Kinematics is still locked because "Vectors & Trig" is not yet mastered
    assert status_map["1D Kinematics"]["unlock_status"] == UnlockStatus.LOCKED.value
    assert len(status_map["1D Kinematics"]["missing_prerequisite_ids"]) == 1

    # 3. Student masters "Vectors & Trig" -> "1D Kinematics" UNLOCKS!
    vec_topic_id = status_map["Vectors & Trig"]["topic_id"]
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=vec_topic_id,
        target_state=LearningState.CALIBRATION,
        trigger="init",
        actor_id=student_id,
        evidence_payload={},
    )
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=vec_topic_id,
        target_state=LearningState.FOUNDATION,
        trigger="init",
        actor_id=student_id,
        evidence_payload={},
    )
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=vec_topic_id,
        target_state=LearningState.PRACTICING,
        trigger="init",
        actor_id=student_id,
        evidence_payload={},
    )
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=vec_topic_id,
        target_state=LearningState.ASSESSMENT,
        trigger="init",
        actor_id=student_id,
        evidence_payload={},
    )
    await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=template.id,
        topic_id=vec_topic_id,
        target_state=LearningState.MASTERY,
        trigger="passed",
        actor_id=student_id,
        evidence_payload={"score": 0.90},
    )


    statuses_after_vec = await TopicDAGService.get_student_unlocked_topics(db_session, template.id, student_id)
    status_map = {s["title"]: s for s in statuses_after_vec}
    assert status_map["1D Kinematics"]["unlock_status"] == UnlockStatus.UNLOCKED.value
    assert status_map["1D Kinematics"]["is_unlocked"] is True

    # 4. Check blocker report on "2D Projectiles"
    proj_topic_id = status_map["2D Projectiles"]["topic_id"]
    blocker_report = await TopicDAGService.get_topic_blocker_report(
        db_session, template.id, proj_topic_id, student_id
    )
    assert blocker_report["is_unlocked"] is False
    assert blocker_report["total_unmastered_ancestors"] == 1
    assert blocker_report["blockers"][0]["title"] == "1D Kinematics"


# ==============================================================================
# 3. FastAPI Endpoint Integration & Role Protection Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_dag_api_endpoints_and_tenant_isolation(
    async_client: AsyncClient,
    multi_topic_curriculum_blueprint: dict,
):
    # 1. Register and login Instructor
    inst_email = f"dag.inst.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": inst_email, "password": "Password123!", "full_name": "Instructor DAG", "role": "instructor"},
    )
    login_inst = await async_client.post(
        "/api/v1/auth/login",
        json={"email": inst_email, "password": "Password123!"},
    )
    inst_token = login_inst.json()["access_token"]

    # 2. Import blueprint
    import_resp = await async_client.post(
        "/api/v1/exam-templates/import",
        json=multi_topic_curriculum_blueprint,
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert import_resp.status_code == 201
    exam = import_resp.json()
    exam_id = exam["id"]

    # 3. Test GET /{template_id}/dag
    dag_resp = await async_client.get(f"/api/v1/exam-templates/{exam_id}/dag")
    assert dag_resp.status_code == 200
    dag_data = dag_resp.json()
    assert dag_data["is_acyclic"] is True
    assert dag_data["total_nodes"] == 4

    # 4. Test GET /{template_id}/learning-path
    path_resp = await async_client.get(f"/api/v1/exam-templates/{exam_id}/learning-path")
    assert path_resp.status_code == 200
    path_data = path_resp.json()
    assert len(path_data["learning_path"]) == 4

    # 5. Register and login Student
    stud_email = f"dag.stud.{uuid.uuid4().hex[:6]}@example.com"
    reg_stud = await async_client.post(
        "/api/v1/auth/register",
        json={"email": stud_email, "password": "Password123!", "full_name": "Student DAG", "role": "student"},
    )
    student_id = reg_stud.json()["id"]
    login_stud = await async_client.post(
        "/api/v1/auth/login",
        json={"email": stud_email, "password": "Password123!"},
    )
    stud_token = login_stud.json()["access_token"]

    # 6. Student queries own unlocked topics
    unlock_resp = await async_client.get(
        f"/api/v1/exam-templates/{exam_id}/unlocked-topics",
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    assert unlock_resp.status_code == 200
    statuses = unlock_resp.json()
    assert len(statuses) == 4

    # 7. Student attempts to inspect another student's unlocks -> MUST BE 403 FORBIDDEN
    fake_student_id = str(uuid.uuid4())
    cross_resp = await async_client.get(
        f"/api/v1/exam-templates/{exam_id}/unlocked-topics?student_id={fake_student_id}",
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    assert cross_resp.status_code == 403

    # 8. Test POST /{template_id}/validate-dag with instructor token
    val_resp = await async_client.post(
        f"/api/v1/exam-templates/{exam_id}/validate-dag",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["is_valid"] is True
    assert val_data["has_cycles"] is False
