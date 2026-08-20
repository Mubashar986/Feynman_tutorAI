# AI-Powered Adaptive Exam Learning Platform
## Product Requirements Document (PRD) + Software Requirements Specification (SRS)

**Document Version:** 1.0  
**Status:** Draft / Baseline Requirements  
**Date:** 2026-08-20  
**Backend Target:** FastAPI / Python  
**Primary Product Goal:** Build a high-quality adaptive learning platform that transforms exam preparation from passive LLM conversation into a structured, measurable, personalized learning process.

---

# 1. Executive Summary

The platform is an AI-powered education system designed primarily for exam preparation. It addresses a fundamental limitation of generic LLM-based learning: a learner can ask questions and receive explanations, but the LLM does not inherently enforce a curriculum, continuously measure mastery, diagnose recurring misconceptions, schedule revision, analyze past papers, or determine what the learner should do next.

The platform will provide those capabilities as a managed learning system.

The product will support multiple exams through reusable exam templates. Each exam template defines its curriculum, subjects, topics, question types, exam structure, scoring rules, learning constraints, and associated resources. Multiple students can use the same exam template simultaneously while maintaining completely independent learning states.

The system will use LLMs as reasoning and content-generation components inside a controlled application architecture rather than treating the LLM itself as the product.

The platform will implement twenty major product capabilities:

1. Adaptive Learning Engine
2. Exam Template Engine
3. Student Mastery Model
4. High-Quality Assessment Engine
5. Resource and Past Paper Intelligence
6. Error Bank and Misconception Tracking
7. Adaptive Revision and Memory
8. Grounded / Source-Aware Tutor
9. Learning Analytics and Readiness
10. AI Quality-Control Layer
11. Personal Learning Twin
12. Misconception Graph
13. Dynamic Knowledge Map
14. Exam Blueprint Reverse Engineering
15. Question Laboratory
16. Multimodal Learning Modes
17. Teach-Back Mode
18. Adversarial Tutor Mode
19. Why-You-Are-Wrong Mode
20. Exam Readiness Simulator

The first implementation should establish a strong, maintainable foundation so these capabilities operate as parts of one coherent learning engine rather than twenty disconnected features.

---

# 2. Product Vision

## 2.1 Vision

Create an AI learning platform that does not merely answer a student's questions, but continuously determines:

- what the student knows;
- what the student does not know;
- why the student is struggling;
- what the student should learn next;
- how that concept should be taught;
- what should be practiced;
- when an old concept should be revisited;
- whether the student has actually mastered the concept;
- how prepared the student is for the target examination.

## 2.2 Product Principle

The central product loop is:

**Exam → Curriculum → Student Model → Learning Decision → Teaching / Assessment → Diagnosis → Repair → Retrieval → Mastery → Readiness → Exam**

All major features should support this loop.

## 2.3 Product Differentiation

The platform must not be designed as:

**User → Chat Interface → LLM → Answer**

It should instead operate as:

**Student → Learning Engine → Specialized Learning Operation → Controlled LLM / Retrieval / Assessment Components → Student Model Update**

This distinction is a core architectural and product requirement.

---

# 3. Product Scope

## 3.1 In Scope

The platform will provide:

- Multiple exam templates.
- Student accounts and independent learning states.
- Structured curriculum and topic maps.
- AI tutoring.
- Resource ingestion and retrieval.
- Past-paper analysis.
- Adaptive learning progression.
- Assessment generation and validation.
- Student mastery tracking.
- Error and misconception tracking.
- Adaptive revision.
- Knowledge visualization.
- Teach-back and adversarial learning modes.
- Multimodal learning experiences.
- Learning analytics.
- Exam readiness estimation.
- AI output quality controls.
- Administrative management of exam templates and resources.
- LLM provider abstraction.
- API-based backend services using FastAPI.

## 3.2 Explicitly Out of Scope for the Baseline

The following are not assumed as platform dependencies:

- WhatsApp.
- Any specific messaging platform.
- A permanent dependency on one LLM provider.
- A permanent dependency on one vector database.
- A permanent dependency on one frontend framework.
- A guarantee of exam success.
- A claim that readiness scores are statistically equivalent to actual probability of passing unless independently validated.

---

# 4. Target Users

## 4.1 Student

A learner preparing for a specific examination.

Primary needs:

- Understand the syllabus.
- Learn concepts.
- Practice questions.
- Identify weaknesses.
- Fix mistakes.
- Revise at the right time.
- Track progress.
- Understand exam readiness.

## 4.2 Content / Exam Administrator

A platform operator who manages exam templates and learning resources.

Primary needs:

- Create and maintain exam definitions.
- Manage topics and subtopics.
- Upload and organize authoritative resources.
- Import and classify past papers.
- Review generated assessment content.
- Monitor content quality.

## 4.3 System Administrator

Responsible for operational management.

Primary needs:

- Manage users.
- Monitor system health.
- Manage model providers.
- Inspect errors.
- Review usage and costs.
- Manage configuration and permissions.

---

# 5. Core Product Concepts

## 5.1 Exam Template

A reusable definition of an examination.

An exam template contains:

- Exam identity.
- Subjects.
- Sections.
- Topics.
- Subtopics.
- Prerequisites.
- Question types.
- Difficulty model.
- Exam timing.
- Scoring rules.
- Topic importance.
- Learning rules.
- Resource associations.
- Past-paper associations.
- Readiness configuration.

A template is shared by many students.

## 5.2 Student Learning State

A student's individualized state for one exam.

It contains:

- Current learning stage.
- Current topic.
- Topic mastery.
- Subtopic mastery.
- Assessment history.
- Error history.
- Misconceptions.
- Revision schedule.
- Learning preferences inferred by the system.
- Readiness indicators.

## 5.3 Learning Session

A sequence of learning interactions associated with a student and an exam.

## 5.4 Learning Stage

A controlled state in the learning process.

Typical stages may include:

- Calibration.
- Foundation.
- Guided Practice.
- Assessment.
- Diagnosis.
- Repair.
- Mastery.
- Revision.

The exact state machine must be configurable without hardcoding an individual exam.

---

# 6. Functional Requirements

## FR-001 Adaptive Learning Engine

The system shall maintain a structured learning state for every student-exam combination.

The system shall determine the next learning action based on:

- Current stage.
- Current topic.
- Topic mastery.
- Previous performance.
- Error patterns.
- Misconceptions.
- Exam importance.
- Revision requirements.
- Assessment history.
- Readiness.
- Available resources.

The system shall not allow an LLM response alone to arbitrarily determine the student's official learning state.

The system shall enforce valid state transitions through application-level logic.

The system shall record every significant learning-state transition.

The system shall support recovery from interrupted learning sessions.

The system shall support configurable mastery thresholds per exam template.

---

## FR-002 Exam Template Engine

The system shall allow authorized administrators to create exam templates.

The system shall allow administrators to define:

- Exam name.
- Exam description.
- Subjects.
- Sections.
- Topics.
- Subtopics.
- Topic relationships.
- Topic importance.
- Prerequisites.
- Question formats.
- Difficulty ranges.
- Scoring rules.
- Time constraints.
- Mastery thresholds.
- Readiness configuration.

The system shall allow multiple students to use the same template concurrently.

The system shall isolate student state from template configuration.

The system shall support versioning of exam templates.

Changes to a template shall not silently corrupt historical student records.

The system shall support at least 20–23 exam templates without requiring exam-specific application logic to be duplicated.

---

## FR-003 Student Mastery Model

The system shall maintain mastery information at topic and, where applicable, subtopic level.

The mastery model shall incorporate:

- Correct answers.
- Incorrect answers.
- Difficulty.
- Recency.
- Repeated attempts.
- Error categories.
- Retrieval performance.
- Teach-back performance where available.

The system shall distinguish between:

- Not studied.
- Learning.
- Weak.
- Needs revision.
- Mastered.

The exact numerical thresholds shall be configurable by exam template.

The system shall retain historical mastery changes.

The system shall allow the learning engine to identify the highest-priority weak areas.

---

## FR-004 High-Quality Assessment Engine

The system shall support generation of assessment items using:

- Exam template.
- Topic.
- Subtopic.
- Difficulty.
- Question type.
- Learning objective.
- Error pattern.
- Source material where required.

The system shall validate generated questions before presenting them to students.

Validation shall include, where applicable:

- Exactly one intended correct answer.
- Answer/explanation consistency.
- Syllabus alignment.
- Appropriate difficulty.
- Ambiguity detection.
- Distractor quality.
- Duplicate detection.
- Source consistency.

The system shall store assessment items independently from generation requests.

The system shall support human review for administrator-approved item banks.

The system shall distinguish generated questions from verified historical/past-paper questions.

---

## FR-005 Resource and Past Paper Intelligence

The system shall allow authorized users to upload learning resources.

Supported resources may include:

- PDFs.
- Text documents.
- Images.
- Notes.
- Past papers.
- Other supported educational documents.

The system shall extract and index usable content.

The system shall associate resources with:

- Exam.
- Subject.
- Topic.
- Subtopic.
- Resource type.
- Source metadata.

The system shall support semantic retrieval over indexed content.

The system shall process past papers separately from generic educational resources.

The system shall extract past-paper questions where technically feasible.

The system shall classify past-paper questions by:

- Topic.
- Question type.
- Difficulty.
- Exam section.
- Year.
- Relevant metadata.

The system shall preserve source provenance.

---

## FR-006 Error Bank and Misconception Tracking

The system shall maintain an error record for significant incorrect responses.

An error record shall support:

- Question.
- Student answer.
- Correct answer.
- Topic.
- Subtopic.
- Error category.
- Suspected misconception.
- Detection timestamp.
- Repair action.
- Subsequent performance.

The system shall detect recurring error patterns.

The system shall allow multiple errors to be associated with the same underlying misconception.

The system shall prioritize recurring misconceptions for remediation.

The system shall track whether a misconception remains active after repair.

---

## FR-007 Adaptive Revision and Memory

The system shall maintain a revision schedule for learned concepts.

Revision scheduling shall consider:

- Mastery.
- Historical performance.
- Time since last successful retrieval.
- Error history.
- Topic importance.
- Exam proximity.
- Recent performance.

The system shall generate revision activities appropriate to the student's current state.

Revision shall include retrieval practice rather than only rereading explanations.

The system shall reintroduce older topics into future learning sessions when appropriate.

---

## FR-008 Grounded / Source-Aware Tutor

The tutoring system shall use retrieved resources when the learning request requires source grounding.

The system shall provide source references where supported by the selected source and UI.

The system shall distinguish between:

- Source-derived information.
- General model knowledge.
- Generated pedagogical explanation.

The system shall avoid presenting unsupported claims as source-backed facts.

For current or changing information, the system shall support a configurable verification mechanism.

The tutor shall adapt its explanation to the student's learning state rather than only responding to the literal question.

---

## FR-009 Learning Analytics and Readiness

The system shall calculate learning analytics for each student-exam combination.

Analytics may include:

- Overall mastery.
- Topic mastery.
- Accuracy.
- Recall performance.
- Error frequency.
- Difficulty performance.
- Learning activity.
- Revision status.
- Weak areas.

The system shall provide actionable recommendations based on analytics.

The system shall identify high-value next actions.

The system shall clearly distinguish measured statistics from model-based estimates.

---

## FR-010 AI Quality-Control Layer

The system shall validate critical LLM-generated outputs before they become authoritative application state.

The quality layer shall support:

- Structured output validation.
- Schema validation.
- Assessment validation.
- Source-grounding checks.
- Consistency checks.
- Duplicate checks.
- Safety checks.
- Retry / regeneration workflows.

The system shall log validation failures.

The system shall prevent malformed structured output from directly corrupting learning state.

The system shall support configurable quality thresholds.

---

## FR-011 Personal Learning Twin

The system shall maintain an evolving learner profile derived from observed learning behavior.

The profile may include:

- Relative strengths.
- Relative weaknesses.
- Typical error patterns.
- Retention behavior.
- Difficulty response.
- Preferred learning modes inferred from performance.
- Response to different teaching strategies.

The system shall use the profile to improve learning decisions.

The system shall distinguish observed behavior from uncertain inference.

The system shall allow the profile to evolve as new evidence is collected.

---

## FR-012 Misconception Graph

The system shall model relationships between:

- Concepts.
- Prerequisites.
- Misconceptions.
- Error types.
- Related concepts.
- Repair strategies.

The system shall allow the learning engine to identify possible upstream causes of repeated errors.

The system shall support propagation of relevant diagnostic information to related topics.

The system shall not treat an inferred misconception as certain without sufficient evidence.

---

## FR-013 Dynamic Knowledge Map

The system shall generate a visual representation of the student's curriculum and knowledge state.

The map shall support:

- Subjects.
- Topics.
- Subtopics.
- Relationships.
- Prerequisites.
- Mastery status.
- Weak areas.
- Revision status.

The system shall update the map as the student's state changes.

The map shall allow students to inspect their learning structure.

---

## FR-014 Exam Blueprint Reverse Engineering

The system shall analyze available past papers and exam resources to identify historical patterns.

The analysis may include:

- Topic frequency.
- Section distribution.
- Question-type distribution.
- Difficulty distribution.
- Recurring concepts.
- Recurring question patterns.
- Historical changes.

The system shall distinguish observed historical patterns from predictions.

The system shall use the resulting blueprint to inform prioritization without presenting predictions as guaranteed future exam content.

---

## FR-015 Question Laboratory

The system shall provide an internal pipeline for controlled assessment generation.

The Question Laboratory shall support:

- Question generation.
- Variant generation.
- Difficulty targeting.
- Topic targeting.
- Distractor generation.
- Validation.
- Duplicate detection.
- Quality scoring.
- Human review.
- Approval.
- Retirement.

The system shall support creation of question families and variants.

The system shall prevent unvalidated questions from entering authoritative question banks where validation is required.

---

## FR-016 Multimodal Learning Modes

The system shall support multiple learning representations where supported by the platform and selected model providers.

Possible modes include:

- Text explanation.
- Visual explanation.
- Audio learning.
- Interactive conversational learning.
- Structured summaries.
- Knowledge maps.

The learning engine shall decide when a different representation may be useful.

Multimodal output shall remain connected to the student's learning state.

The system shall not generate multimodal content merely for novelty when a simpler learning intervention is more appropriate.

---

## FR-017 Teach-Back Mode

The system shall allow the student to explain a concept in their own words.

The system shall evaluate the explanation against the relevant learning objective.

The system shall identify:

- Correct understanding.
- Missing elements.
- Contradictions.
- Misconceptions.
- Superficial or incomplete explanations.

The system shall provide targeted feedback.

Teach-back performance shall contribute to the student model where appropriate.

---

## FR-018 Adversarial Tutor Mode

The system shall support a learning mode in which the tutor intentionally challenges the student's reasoning.

The system may introduce:

- Counterexamples.
- Edge cases.
- Alternative interpretations.
- Changed conditions.
- Follow-up challenges.

The system shall evaluate whether the student can defend or revise their reasoning.

The system shall connect performance to the relevant learning objective and mastery model.

---

## FR-019 Why-You-Are-Wrong Mode

For incorrect answers, the system shall provide diagnostic feedback rather than only revealing the correct answer.

Where sufficient evidence exists, the system shall explain:

- What the student selected.
- Why that selection is incorrect.
- What reasoning pattern likely produced the error.
- What recognition rule or concept should be used instead.
- A targeted repair activity.

The system shall avoid claiming certainty about the student's internal reasoning when only the answer is known.

---

## FR-020 Exam Readiness Simulator

The system shall provide an exam-readiness assessment based on available evidence.

Readiness shall consider, where applicable:

- Topic mastery.
- Accuracy.
- Recall.
- Difficulty performance.
- Speed.
- Weak-topic concentration.
- Exam structure.
- Historical performance.

The system shall identify major risk areas.

The system shall recommend high-value preparation actions.

The system shall distinguish readiness estimates from guaranteed examination outcomes.

If statistical probability of passing is ever introduced, it shall require independent validation before being presented as a calibrated probability.

---

# 7. Cross-Cutting Functional Requirements

## FR-021 Authentication and Authorization

The system shall support secure user authentication.

The system shall support role-based authorization for:

- Student.
- Content administrator.
- System administrator.

Users shall only access data permitted by their role.

Students shall only access their own learning records.

## FR-022 Multi-User Isolation

The system shall support concurrent use by multiple students.

Student state shall remain isolated.

Shared exam templates and resources shall not contain student-specific state.

## FR-023 LLM Provider Abstraction

The application shall separate learning logic from individual LLM providers.

The system should support configurable model providers.

Provider-specific implementation details shall not be embedded throughout business logic.

The platform shall record model/provider metadata for important generated outputs.

## FR-024 Observability

The system shall record:

- API errors.
- LLM errors.
- Validation failures.
- Learning-state transitions.
- Assessment outcomes.
- Retrieval operations.
- Processing latency.
- Resource-processing failures.

Sensitive information shall not be unnecessarily included in logs.

## FR-025 Auditability

Important learning-state changes and administrator actions shall be auditable.

The system shall preserve enough information to explain why a major learning decision was made.

---

# 8. Non-Functional Requirements

## NFR-001 Maintainability

The architecture shall separate:

- API layer.
- Domain logic.
- Learning engine.
- Assessment engine.
- Retrieval layer.
- LLM integration.
- Persistence.
- Background processing.

Business logic shall not be tightly coupled to the HTTP framework.

## NFR-002 Scalability

The architecture shall support many students using the same exam template concurrently.

Shared resources shall be reusable.

Student-specific state shall scale independently from static exam configuration.

## NFR-003 Performance

Interactive learning operations should provide predictable response times.

Long-running operations such as:

- document ingestion;
- large-scale question generation;
- blueprint analysis;
- multimodal generation;

shall be capable of asynchronous processing.

Exact latency targets shall be finalized during architecture and capacity planning.

## NFR-004 Reliability

The system shall gracefully handle:

- LLM timeouts.
- Provider failures.
- Retrieval failures.
- malformed model output.
- database failures.
- interrupted learning sessions.

The system shall not silently advance a student when a critical learning-state update fails.

## NFR-005 Security

The system shall protect:

- student accounts;
- uploaded educational resources;
- learning history;
- generated content;
- administrative configuration.

Authorization shall be enforced server-side.

Uploaded files shall be treated as untrusted input.

## NFR-006 Data Integrity

Learning state transitions shall be atomic where necessary.

Assessment results shall not be overwritten without an audit trail.

Historical learning records shall remain consistent with the template version under which they were generated.

## NFR-007 Extensibility

Adding a new exam should primarily require configuration/content rather than application-code duplication.

Adding a new LLM provider should not require rewriting the learning engine.

Adding a new learning mode should not require redesigning the student data model.

## NFR-008 Explainability

The platform shall provide enough internal evidence to explain important decisions such as:

- Why a topic was selected.
- Why a revision was scheduled.
- Why a student was classified as weak.
- Why an assessment item was rejected.

## NFR-009 Quality

The system shall prioritize correctness and educational usefulness over maximum generation volume.

Generated educational content shall be validated according to its risk and use.

---

# 9. Data Requirements

The conceptual data model shall include at least:

## User

- id
- role
- account metadata
- authentication metadata

## ExamTemplate

- id
- version
- name
- description
- configuration
- status

## Subject

- id
- exam_template_id
- name
- metadata

## Topic

- id
- subject_id
- parent_topic_id
- name
- learning objectives
- importance
- prerequisites

## Resource

- id
- exam_template_id
- type
- metadata
- processing status
- source information

## ResourceChunk

- id
- resource_id
- content
- metadata
- embedding reference

## PastPaper

- id
- exam_template_id
- year
- metadata

## Question

- id
- source
- topic
- difficulty
- question_type
- options
- answer
- explanation
- validation status

## StudentExam

- id
- student_id
- exam_template_id
- template_version
- current_stage
- current_topic
- readiness data

## MasteryRecord

- student_exam_id
- topic_id
- mastery state
- evidence
- historical measurements

## Attempt

- student_exam_id
- question_id
- response
- correctness
- timestamp
- response metadata

## ErrorRecord

- attempt_id
- error_type
- misconception_id
- repair status

## Misconception

- id
- concept
- description
- evidence
- confidence

## RevisionItem

- student_exam_id
- topic_id
- scheduled_at
- reason
- status

## LearningEvent

- student_exam_id
- event_type
- event data
- timestamp

---

# 10. Core Learning Workflow

A typical learning cycle shall follow this conceptual process:

1. Student selects an exam.
2. System loads the exam template.
3. System initializes or retrieves the student's learning state.
4. System determines the current learning stage.
5. System selects the next learning objective.
6. System retrieves relevant resources when required.
7. Tutor delivers an appropriate learning intervention.
8. Student performs an activity.
9. Assessment results are recorded.
10. System diagnoses errors.
11. Mastery is updated.
12. Misconceptions are updated when evidence is sufficient.
13. System determines whether repair is required.
14. System schedules revision where appropriate.
15. System determines the next learning action.
16. Readiness analytics are updated.

The LLM may assist with teaching, generation, classification, and reasoning, but the application remains responsible for authoritative state.

---

# 11. Resource Processing Workflow

A resource ingestion pipeline shall conceptually follow:

1. Upload.
2. File validation.
3. Metadata registration.
4. Content extraction.
5. Structural analysis.
6. Chunking.
7. Metadata enrichment.
8. Embedding/indexing.
9. Topic association.
10. Quality/status verification.
11. Availability for retrieval.

Past papers shall additionally support:

1. Question extraction.
2. Question boundary detection.
3. Question classification.
4. Topic mapping.
5. Difficulty estimation.
6. Historical metadata association.

---

# 12. Assessment Lifecycle

An assessment item shall progress through states such as:

Draft → Generated → Validating → Validated → Approved → Published → Retired

The exact lifecycle shall be configurable.

A failed validation shall not be treated as a successful item.

---

# 13. Learning-State Lifecycle

A student learning state shall support controlled transitions such as:

Calibration → Foundation → Practice → Assessment → Diagnosis → Repair → Mastery → Revision

Transitions shall be determined by configurable rules and evidence.

The system shall prevent invalid transitions.

---

# 14. AI Interaction Principles

## 14.1 LLM Is a Component, Not the System

The platform shall not rely on a single unrestricted prompt as its primary architecture.

## 14.2 Structured Outputs

Critical LLM operations shall use structured schemas where practical.

## 14.3 Retrieval Before Generation

When source grounding is required, retrieval shall occur before final generation.

## 14.4 Validation Before Persistence

Generated outputs shall be validated before being used as authoritative system state.

## 14.5 Evidence-Based Personalization

Personalization shall be based on observed student data rather than arbitrary model assumptions.

## 14.6 Uncertainty

The system shall represent uncertain inferences as uncertain.

---

# 15. Product Experience Requirements

The student experience should make the system feel like a tutor and preparation system rather than a generic chatbot.

The primary interface should emphasize:

- Current goal.
- Current topic.
- Current activity.
- Immediate feedback.
- Progress.
- Weaknesses.
- Next action.

The system should minimize the amount of prompting knowledge required from the student.

A student should not need to know how to write sophisticated prompts to receive sophisticated learning behavior.

This is one of the central reasons the product exists.

---

# 16. Administrator Experience Requirements

Administrators shall be able to:

- Create exam templates.
- Edit curriculum structures.
- Upload resources.
- Manage past papers.
- Review extracted questions.
- Inspect generated questions.
- Approve or reject assessment items.
- Configure learning thresholds.
- Inspect resource processing status.
- Monitor quality failures.

---

# 17. Frontend Requirements

The frontend architecture shall support at least:

1. Authentication.
2. Exam selection.
3. Dashboard.
4. Learning session.
5. Question/assessment interface.
6. Explanation interface.
7. Progress dashboard.
8. Error bank.
9. Revision center.
10. Knowledge map.
11. Exam blueprint.
12. Readiness dashboard.
13. Resource browser.
14. Student learning profile.
15. Administrative interfaces.

The final visual design system shall be defined separately during frontend design.

---

# 18. API Requirements

The FastAPI backend shall expose logically separated APIs for:

- Authentication.
- Users.
- Exams.
- Subjects.
- Topics.
- Resources.
- Retrieval.
- Learning sessions.
- Learning-state management.
- Questions.
- Assessments.
- Attempts.
- Errors.
- Misconceptions.
- Revision.
- Analytics.
- Readiness.
- Administration.

The API contract shall be versioned.

---

# 19. Background Processing Requirements

The platform shall support asynchronous processing for operations that may exceed normal interactive request duration.

Candidate operations include:

- Resource ingestion.
- Embedding generation.
- Past-paper extraction.
- Blueprint analysis.
- Bulk question generation.
- Question validation.
- Audio generation.
- Video generation.
- Large analytics jobs.

The exact task queue and worker technology shall be selected during architecture design.

---

# 20. Quality Assurance Requirements

Testing shall include:

## Unit Testing

- State transitions.
- Mastery calculations.
- Revision rules.
- Question validation.
- Exam-template rules.
- Domain services.

## Integration Testing

- Database interactions.
- Retrieval pipeline.
- LLM adapters.
- Resource processing.
- Assessment lifecycle.

## End-to-End Testing

- Student registration.
- Exam enrollment.
- Learning session.
- Assessment.
- Error diagnosis.
- Repair.
- Revision.
- Readiness.

## AI Evaluation

The platform shall maintain evaluation datasets for:

- Question quality.
- Answer correctness.
- Grounding.
- Explanation quality.
- Error classification.
- Misconception detection.
- Teach-back evaluation.

AI evaluation shall not rely exclusively on subjective manual inspection.

---

# 21. Security Requirements

The system shall:

- Authenticate users securely.
- Authorize every protected operation.
- Isolate student data.
- Validate uploaded files.
- Protect API credentials.
- Avoid exposing provider secrets to clients.
- Apply appropriate rate limiting.
- Log security-relevant events.
- Protect administrative endpoints.
- Prevent unauthorized resource access.

---

# 22. Privacy Requirements

The platform shall minimize collection of unnecessary personal data.

Student learning records shall be treated as private user data.

LLM providers shall only receive data required for the requested operation, subject to the selected provider's data-processing configuration.

The platform shall document which data is sent to external model providers.

Data retention and deletion policies shall be defined before production launch.

---

# 23. Observability Requirements

The platform shall provide visibility into:

- API latency.
- Error rate.
- LLM latency.
- LLM token usage where available.
- LLM cost where available.
- Retrieval latency.
- Retrieval failures.
- Queue depth.
- Resource processing failures.
- Assessment validation failures.
- Learning-state transition failures.

Observability data shall support debugging without exposing unnecessary student content.

---

# 24. Product Success Metrics

The following metrics should be established and measured:

## Learning Metrics

- Improvement between diagnostic and later assessment.
- Mastery progression.
- Retention performance.
- Reduction in recurring errors.
- Repair success rate.
- Revision effectiveness.

## Assessment Metrics

- Question validation failure rate.
- Question duplication rate.
- Human rejection rate.
- Answer/explanation inconsistency rate.

## Product Metrics

- Learning-session completion.
- Return learning sessions.
- Topic completion.
- Revision completion.
- Resource usage.
- Feature usage.

## System Metrics

- API latency.
- Error rate.
- LLM failure rate.
- Cost per learning session.
- Resource-processing success rate.

No metric should be interpreted as proof of educational effectiveness without an appropriate evaluation design.

---

# 25. Risks and Mitigations

## Risk: LLM Hallucination

Mitigation:

- Retrieval.
- Source grounding.
- Validation.
- Provider abstraction.
- Human review for high-risk content.

## Risk: Poorly Generated Questions

Mitigation:

- Question Laboratory.
- Automated validation.
- Evaluation datasets.
- Human approval where necessary.

## Risk: Incorrect Student Diagnosis

Mitigation:

- Evidence aggregation.
- Confidence levels.
- Repeated observations.
- Avoiding absolute claims from single responses.

## Risk: Overengineering

Mitigation:

- Keep the learning engine modular.
- Introduce infrastructure only when justified.
- Separate domain architecture from infrastructure choices.

## Risk: Template Explosion

Mitigation:

- Configuration-driven exam templates.
- Shared learning engine.
- Versioned schemas.

## Risk: Vendor Lock-In

Mitigation:

- LLM abstraction.
- Retrieval abstraction.
- Storage abstraction where practical.

## Risk: Stale Knowledge

Mitigation:

- Resource versioning.
- Source metadata.
- Configurable verification mechanisms.

---

# 26. Architectural Constraints

The following are current product constraints:

1. Backend target is FastAPI/Python.
2. The system must support multiple exam templates.
3. Templates must be reusable across many students.
4. Student learning state must remain isolated.
5. The learning process must be stateful.
6. LLMs are components of the system, not the authoritative source of application state.
7. RAG/source grounding is required for relevant resource-based learning.
8. Past papers are first-class learning data.
9. Quality validation is required for important generated content.
10. Architecture must remain extensible to additional exams and learning modes.
11. WhatsApp is not a system dependency.
12. The platform should not be architecturally locked to a single LLM provider.

---

# 27. Open Design Decisions for the Architecture Phase

The following are intentionally not finalized by this SRS:

- PostgreSQL vs other primary database technology.
- Redis usage and exact caching strategy.
- Vector database technology.
- Background task framework.
- Message broker.
- LLM provider selection.
- Embedding provider.
- Frontend framework.
- Object storage provider.
- Deployment platform.
- Exact authentication provider.
- Exact IRT/adaptive-testing implementation.
- Exact readiness-calibration methodology.
- Exact multimodal generation providers.

These decisions belong to the system architecture and technical design phase.

---

# 28. Recommended Architectural Boundaries

The eventual system should conceptually separate the following domains:

1. Identity and Access
2. Exam Configuration
3. Curriculum / Knowledge Model
4. Student Learning State
5. Learning Orchestration
6. Assessment
7. Error and Misconception Intelligence
8. Resource Management
9. Retrieval
10. AI / LLM Integration
11. Revision
12. Analytics
13. Readiness
14. Administration
15. Observability

These boundaries are conceptual and should not automatically be interpreted as separate microservices.

---

# 29. Definition of Done for the Product Specification

The product specification will be considered sufficiently defined when:

- All twenty product capabilities have explicit requirements.
- Student and exam concepts are clearly separated.
- Learning-state behavior is defined.
- Assessment lifecycle is defined.
- Resource lifecycle is defined.
- AI quality controls are defined.
- Security and privacy requirements are defined.
- Product metrics are defined.
- Architectural constraints are explicit.
- Remaining implementation decisions are isolated as architecture decisions.

---

# 30. Future Architecture Phase

The next phase shall transform this PRD/SRS into a technical system design covering:

1. System context diagram.
2. Container/component architecture.
3. Domain model.
4. Database schema.
5. FastAPI project structure.
6. Learning-state machine.
7. LLM orchestration architecture.
8. RAG pipeline.
9. Assessment pipeline.
10. Student mastery architecture.
11. Misconception graph.
12. Revision engine.
13. Analytics architecture.
14. Readiness model.
15. Background-job architecture.
16. Caching strategy.
17. API design.
18. Authentication and authorization.
19. Frontend architecture.
20. Deployment architecture.
21. Observability.
22. Testing architecture.
23. CI/CD.
24. Cost and scaling model.

---

# 31. Final Product Principle

The product must not compete with generic LLMs by attempting to become a larger chatbot.

Its core value is the structured learning system surrounding the LLM.

The system should continuously transform:

**Student interaction → Evidence → Diagnosis → Learning decision → Intervention → New evidence**

The LLM provides powerful language, reasoning, generation, and explanation capabilities.

The platform provides:

**Structure, memory, assessment, personalization, progression, grounding, diagnosis, quality control, and readiness.**

That distinction is the foundation of the product.
