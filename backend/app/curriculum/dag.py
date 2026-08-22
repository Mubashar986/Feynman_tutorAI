from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import (
    ExamTemplate,
    Subject,
    Topic,
    TopicDifficulty,
    TopicPrerequisite,
)
from backend.app.learning_state.models import LearningState, StudentLearningState


class UnlockStatus(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    MASTERED = "mastered"


@dataclass
class TopicDAGNode:
    """In-memory representation of a node in the topic dependency graph."""
    topic_id: str
    title: str
    subject_id: str
    difficulty: TopicDifficulty = TopicDifficulty.INTERMEDIATE
    estimated_hours: float = 4.0
    importance_weight: float = 1.0
    in_degree: int = 0
    out_degree: int = 0
    level: int = 0
    prerequisite_ids: Set[str] = field(default_factory=set)
    dependent_ids: Set[str] = field(default_factory=set)


class TopicDAG:
    """
    Pure Python Directed Acyclic Graph (DAG) for managing curriculum topic dependencies.
    Implements Kahn's algorithm, DFS 3-coloring cycle detection, topological sorting,
    and prerequisite ancestor reachability.
    """

    def __init__(self):
        self.nodes: Dict[str, TopicDAGNode] = {}
        self.forward_adj: Dict[str, Set[str]] = defaultdict(set)  # u -> {v} where u is prereq of v
        self.inverse_adj: Dict[str, Set[str]] = defaultdict(set)  # v -> {u} where u is prereq of v
        self.mandatory_edges: Set[Tuple[str, str]] = set()  # (prereq_id, topic_id)

    def add_node(
        self,
        topic_id: str,
        title: str,
        subject_id: str,
        difficulty: TopicDifficulty = TopicDifficulty.INTERMEDIATE,
        estimated_hours: float = 4.0,
        importance_weight: float = 1.0,
    ) -> TopicDAGNode:
        if topic_id not in self.nodes:
            node = TopicDAGNode(
                topic_id=topic_id,
                title=title,
                subject_id=subject_id,
                difficulty=difficulty,
                estimated_hours=estimated_hours,
                importance_weight=importance_weight,
            )
            self.nodes[topic_id] = node
        return self.nodes[topic_id]

    def add_edge(self, prerequisite_id: str, topic_id: str, is_mandatory: bool = True) -> None:
        """
        Adds a directed dependency edge: prerequisite_id -> topic_id (prerequisite_id must precede topic_id).
        """
        if prerequisite_id == topic_id:
            # Self-loop edge
            self.forward_adj[prerequisite_id].add(topic_id)
            self.inverse_adj[topic_id].add(prerequisite_id)
            return

        self.forward_adj[prerequisite_id].add(topic_id)
        self.inverse_adj[topic_id].add(prerequisite_id)

        if prerequisite_id in self.nodes:
            self.nodes[prerequisite_id].dependent_ids.add(topic_id)
        if topic_id in self.nodes:
            self.nodes[topic_id].prerequisite_ids.add(prerequisite_id)

        if is_mandatory:
            self.mandatory_edges.add((prerequisite_id, topic_id))

    def detect_cycles(self) -> Tuple[bool, Optional[List[str]]]:
        """
        Detects if the graph contains cycles using Kahn's algorithm.
        Returns (has_cycles: bool, cycle_path: Optional[List[str]]).
        """
        # 1. Compute in-degrees
        in_degree = {node_id: len(self.inverse_adj[node_id]) for node_id in self.nodes}

        # 2. Check for immediate self-loops
        for node_id in self.nodes:
            if node_id in self.forward_adj[node_id]:
                return True, [node_id, node_id]

        # 3. Queue nodes with in-degree 0
        queue = deque([node_id for node_id, deg in in_degree.items() if deg == 0])
        processed_count = 0

        while queue:
            curr = queue.popleft()
            processed_count += 1

            for neighbor in self.forward_adj[curr]:
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        if processed_count == len(self.nodes):
            return False, None

        # Cycle exists; extract cycle path using DFS 3-coloring
        cycle_path = self._extract_cycle_path_dfs()
        return True, cycle_path

    def _extract_cycle_path_dfs(self) -> Optional[List[str]]:
        """
        Extracts the exact list of node IDs forming a cycle using DFS 3-coloring.
        WHITE = 0 (unvisited), GRAY = 1 (active in stack), BLACK = 2 (completed).
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {node_id: WHITE for node_id in self.nodes}
        path = []

        def dfs(node_id: str) -> Optional[List[str]]:
            colors[node_id] = GRAY
            path.append(node_id)

            for neighbor in self.forward_adj[node_id]:
                if neighbor not in colors:
                    continue
                if colors[neighbor] == GRAY:
                    # Found back-edge!
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
                elif colors[neighbor] == WHITE:
                    found = dfs(neighbor)
                    if found:
                        return found

            colors[node_id] = BLACK
            path.pop()
            return None

        for n_id in self.nodes:
            if colors[n_id] == WHITE:
                res = dfs(n_id)
                if res:
                    return res
        return None

    def get_topological_order(self) -> List[TopicDAGNode]:
        """
        Returns all nodes in a valid topological dependency order.
        Raises ValueError if graph contains a cycle.
        """
        has_cycle, cycle_path = self.detect_cycles()
        if has_cycle:
            raise ValueError(f"Cannot compute topological order: Cycle detected {cycle_path}")

        in_degree = {node_id: len(self.inverse_adj[node_id]) for node_id in self.nodes}
        # Zero-in-degree queue sorted by original topic order/title for deterministic sorting
        queue = deque(
            sorted([node_id for node_id, deg in in_degree.items() if deg == 0])
        )
        order = []

        while queue:
            curr = queue.popleft()
            order.append(self.nodes[curr])

            for neighbor in sorted(self.forward_adj[curr]):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return order

    def compute_node_levels(self) -> Dict[str, int]:
        """
        Computes the depth level (longest path from any root) for each node.
        Root nodes have level 0; children have level = max(parent.level) + 1.
        """
        topo_order = self.get_topological_order()
        levels: Dict[str, int] = {node.topic_id: 0 for node in topo_order}

        for node in topo_order:
            curr_id = node.topic_id
            curr_level = levels[curr_id]
            node.level = curr_level

            for dependent_id in self.forward_adj[curr_id]:
                if dependent_id in levels:
                    levels[dependent_id] = max(levels[dependent_id], curr_level + 1)
                    if dependent_id in self.nodes:
                        self.nodes[dependent_id].level = levels[dependent_id]

        # Update in_degree and out_degree on nodes
        for node_id, node in self.nodes.items():
            node.in_degree = len(self.inverse_adj[node_id])
            node.out_degree = len(self.forward_adj[node_id])

        return levels

    def get_prerequisite_ancestors(self, target_topic_id: str) -> Set[str]:
        """
        Performs reverse BFS to find all direct and indirect prerequisite ancestors of target_topic_id.
        """
        ancestors: Set[str] = set()
        queue = deque(self.inverse_adj[target_topic_id])

        while queue:
            curr = queue.popleft()
            if curr not in ancestors and curr in self.nodes:
                ancestors.add(curr)
                for parent in self.inverse_adj[curr]:
                    if parent not in ancestors:
                        queue.append(parent)

        return ancestors

    def get_root_node_ids(self) -> List[str]:
        """Returns all node IDs with in-degree == 0."""
        return [node_id for node_id, node in self.nodes.items() if len(self.inverse_adj[node_id]) == 0]

    def get_terminal_node_ids(self) -> List[str]:
        """Returns all node IDs with out-degree == 0."""
        return [node_id for node_id, node in self.nodes.items() if len(self.forward_adj[node_id]) == 0]


class TopicDAGService:
    """
    Application domain service for orchestrating curriculum DAG operations and student unlock checks.
    """

    @classmethod
    async def build_dag_for_exam(
        cls,
        session: AsyncSession,
        exam_template_id: str,
    ) -> Tuple[ExamTemplate, TopicDAG]:
        """
        Loads all topics and prerequisite edges for an exam template and constructs a TopicDAG instance.
        """
        stmt_template = select(ExamTemplate).where(
            (ExamTemplate.id == exam_template_id) | (ExamTemplate.code == exam_template_id)
        )
        res_template = await session.execute(stmt_template)
        template = res_template.scalar_one_or_none()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exam template '{exam_template_id}' not found",
            )

        # 1. Fetch all subjects for this template
        stmt_subjs = select(Subject).where(Subject.exam_template_id == template.id)
        res_subjs = await session.execute(stmt_subjs)
        subjects = res_subjs.scalars().all()
        subject_ids = [s.id for s in subjects]

        dag = TopicDAG()

        if not subject_ids:
            return template, dag

        # 2. Fetch all topics for these subjects
        stmt_topics = select(Topic).where(Topic.subject_id.in_(subject_ids))
        res_topics = await session.execute(stmt_topics)
        topics = res_topics.scalars().all()
        topic_ids = [t.id for t in topics]

        for t in topics:
            dag.add_node(
                topic_id=t.id,
                title=t.title,
                subject_id=t.subject_id,
                difficulty=t.difficulty,
                estimated_hours=t.estimated_hours,
                importance_weight=t.importance_weight,
            )

        if not topic_ids:
            return template, dag

        # 3. Fetch all prerequisite edges between these topics
        stmt_prereqs = select(TopicPrerequisite).where(
            (TopicPrerequisite.topic_id.in_(topic_ids)) & (TopicPrerequisite.prerequisite_topic_id.in_(topic_ids))
        )
        res_prereqs = await session.execute(stmt_prereqs)
        prereqs = res_prereqs.scalars().all()

        for p in prereqs:
            dag.add_edge(
                prerequisite_id=p.prerequisite_topic_id,
                topic_id=p.topic_id,
                is_mandatory=p.is_mandatory,
            )

        return template, dag

    @classmethod
    async def get_dag_graph(
        cls,
        session: AsyncSession,
        exam_template_id: str,
    ) -> Dict:
        """
        Builds the DAG, computes depth levels, and returns the full graph payload for visual UI renderers.
        """
        template, dag = await cls.build_dag_for_exam(session, exam_template_id)
        has_cycles, cycle_path = dag.detect_cycles()

        if not has_cycles and len(dag.nodes) > 0:
            dag.compute_node_levels()

        nodes_data = []
        for node_id, node in dag.nodes.items():
            nodes_data.append({
                "id": node.topic_id,
                "title": node.title,
                "subject_id": node.subject_id,
                "difficulty": node.difficulty.value,
                "estimated_hours": node.estimated_hours,
                "importance_weight": node.importance_weight,
                "in_degree": len(dag.inverse_adj[node_id]),
                "out_degree": len(dag.forward_adj[node_id]),
                "level": node.level,
                "prerequisite_ids": list(dag.inverse_adj[node_id]),
                "dependent_ids": list(dag.forward_adj[node_id]),
            })

        edges_data = []
        for prereq_id, targets in dag.forward_adj.items():
            for target_id in targets:
                edges_data.append({
                    "id": f"{prereq_id}->{target_id}",
                    "source": prereq_id,
                    "target": target_id,
                    "is_mandatory": (prereq_id, target_id) in dag.mandatory_edges,
                })

        return {
            "exam_template_id": template.id,
            "exam_title": template.title,
            "is_acyclic": not has_cycles,
            "cycle_path": cycle_path,
            "total_nodes": len(dag.nodes),
            "total_edges": len(edges_data),
            "root_topic_ids": dag.get_root_node_ids(),
            "terminal_topic_ids": dag.get_terminal_node_ids(),
            "nodes": nodes_data,
            "edges": edges_data,
        }

    @classmethod
    async def get_learning_path(
        cls,
        session: AsyncSession,
        exam_template_id: str,
    ) -> Dict:
        """
        Computes the canonical topological study sequence for the curriculum.
        """
        template, dag = await cls.build_dag_for_exam(session, exam_template_id)
        has_cycles, cycle_path = dag.detect_cycles()
        if has_cycles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot generate learning path: Directed cycle detected in curriculum: {cycle_path}",
            )

        dag.compute_node_levels()
        topo_order = dag.get_topological_order()

        path_nodes = []
        for idx, node in enumerate(topo_order, start=1):
            path_nodes.append({
                "sequence_number": idx,
                "topic_id": node.topic_id,
                "title": node.title,
                "subject_id": node.subject_id,
                "difficulty": node.difficulty.value,
                "estimated_hours": node.estimated_hours,
                "level": node.level,
                "prerequisite_ids": list(dag.inverse_adj[node.topic_id]),
            })

        return {
            "exam_template_id": template.id,
            "exam_title": template.title,
            "total_topics": len(path_nodes),
            "learning_path": path_nodes,
        }

    @classmethod
    async def get_student_unlocked_topics(
        cls,
        session: AsyncSession,
        exam_template_id: str,
        student_id: str,
    ) -> List[Dict]:
        """
        Evaluates which topics are LOCKED, UNLOCKED, or MASTERED for a specific student.
        A topic is UNLOCKED if all its mandatory prerequisites are in MASTERY state.
        """
        template, dag = await cls.build_dag_for_exam(session, exam_template_id)
        if not dag.nodes:
            return []

        # 1. Fetch student's learning state records for this exam
        stmt_states = select(StudentLearningState).where(
            (StudentLearningState.student_id == student_id) &
            (StudentLearningState.exam_template_id == template.id)
        )
        res_states = await session.execute(stmt_states)
        student_states = res_states.scalars().all()
        
        mastered_topic_ids: Set[str] = {
            s.topic_id for s in student_states if s.current_state == LearningState.MASTERY
        }
        state_by_topic: Dict[str, LearningState] = {
            s.topic_id: s.current_state for s in student_states
        }


        # 2. Evaluate status for each node
        results = []
        for node_id, node in dag.nodes.items():
            current_state = state_by_topic.get(node_id, LearningState.NOT_STARTED)
            prereq_ids = dag.inverse_adj[node_id]
            missing_mandatory_prereqs = [
                p_id for p_id in prereq_ids
                if (p_id, node_id) in dag.mandatory_edges and p_id not in mastered_topic_ids
            ]

            if current_state == LearningState.MASTERY:
                status_val = UnlockStatus.MASTERED
                is_unlocked = True
            elif len(missing_mandatory_prereqs) == 0:
                status_val = UnlockStatus.UNLOCKED
                is_unlocked = True
            else:
                status_val = UnlockStatus.LOCKED
                is_unlocked = False

            # Get titles of blocking prerequisites
            blocking_titles = [
                dag.nodes[p_id].title for p_id in missing_mandatory_prereqs
                if p_id in dag.nodes
            ]

            results.append({
                "topic_id": node_id,
                "title": node.title,
                "subject_id": node.subject_id,
                "difficulty": node.difficulty.value,
                "level": node.level,
                "current_learning_state": current_state.value,
                "unlock_status": status_val.value,
                "is_unlocked": is_unlocked,
                "missing_prerequisite_ids": missing_mandatory_prereqs,
                "missing_prerequisite_titles": blocking_titles,
            })

        return results

    @classmethod
    async def get_topic_blocker_report(
        cls,
        session: AsyncSession,
        exam_template_id: str,
        topic_id: str,
        student_id: str,
    ) -> Dict:
        """
        Analyzes a single topic for a student, returning its ancestral prerequisite blocker tree.
        """
        template, dag = await cls.build_dag_for_exam(session, exam_template_id)
        if topic_id not in dag.nodes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found in exam template '{exam_template_id}'",
            )

        target_node = dag.nodes[topic_id]

        # Fetch student mastery states
        stmt_states = select(StudentLearningState).where(
            (StudentLearningState.student_id == student_id) &
            (StudentLearningState.exam_template_id == template.id)
        )
        res_states = await session.execute(stmt_states)
        student_states = res_states.scalars().all()
        mastered_topic_ids: Set[str] = {
            s.topic_id for s in student_states if s.current_state == LearningState.MASTERY
        }
        state_by_topic: Dict[str, LearningState] = {
            s.topic_id: s.current_state for s in student_states
        }


        # Collect all prerequisite ancestors
        ancestor_ids = dag.get_prerequisite_ancestors(topic_id)
        unmastered_blockers = []

        for anc_id in sorted(ancestor_ids):
            if anc_id not in mastered_topic_ids and anc_id in dag.nodes:
                anc_node = dag.nodes[anc_id]
                unmastered_blockers.append({
                    "topic_id": anc_id,
                    "title": anc_node.title,
                    "difficulty": anc_node.difficulty.value,
                    "level": anc_node.level,
                    "current_state": state_by_topic.get(anc_id, LearningState.NOT_STARTED).value,
                    "is_direct_prerequisite": anc_id in dag.inverse_adj[topic_id],
                })

        is_unlocked = len([b for b in unmastered_blockers if b["is_direct_prerequisite"]]) == 0

        return {
            "target_topic_id": topic_id,
            "target_topic_title": target_node.title,
            "exam_template_id": template.id,
            "student_id": student_id,
            "is_unlocked": is_unlocked,
            "total_unmastered_ancestors": len(unmastered_blockers),
            "blockers": unmastered_blockers,
        }

    @classmethod
    async def validate_exam_dag(
        cls,
        session: AsyncSession,
        exam_template_id: str,
    ) -> Dict:
        """
        Audits graph integrity, cycles, connectivity, and terminal nodes for an exam template.
        """
        template, dag = await cls.build_dag_for_exam(session, exam_template_id)
        has_cycles, cycle_path = dag.detect_cycles()

        levels = {}
        if not has_cycles and len(dag.nodes) > 0:
            levels = dag.compute_node_levels()

        return {
            "exam_template_id": template.id,
            "exam_title": template.title,
            "is_valid": not has_cycles,
            "has_cycles": has_cycles,
            "cycle_path": cycle_path,
            "total_topics": len(dag.nodes),
            "total_prerequisite_edges": len(dag.mandatory_edges),
            "root_topic_ids": dag.get_root_node_ids(),
            "terminal_topic_ids": dag.get_terminal_node_ids(),
            "max_depth_level": max(levels.values()) if levels else 0,
        }
