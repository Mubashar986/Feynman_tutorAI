/**
 * Types and models for the Exam Template Catalog & Syllabus Taxonomy.
 */

export type ExamBoard = "Cambridge International" | "College Board" | "AQA" | "IB" | "AAMC";

export type BloomLevel = "Remember" | "Understand" | "Apply" | "Analyze" | "Evaluate" | "Create";

export type TopicDifficulty = "foundational" | "intermediate" | "advanced";

export interface LearningObjective {
  id: string;
  code: string; // e.g. "9702.4.1"
  description: string;
  formulaLatex?: string;
  bloomLevel: BloomLevel;
}

export interface TopicPrerequisite {
  topicId: string;
  prerequisiteTopicId: string;
  prerequisiteTopicTitle: string;
  isMandatory: boolean;
}

export interface Topic {
  id: string;
  subjectId: string;
  title: string;
  order: number;
  difficulty: TopicDifficulty;
  estimatedHours: number;
  description?: string;
  prerequisites: TopicPrerequisite[];
  objectives: LearningObjective[];
}

export interface Subject {
  id: string;
  examTemplateId: string;
  title: string;
  order: number;
  description: string;
  topics: Topic[];
}

export interface ExamTemplate {
  id: string;
  title: string;
  code: string; // e.g. "9702"
  board: ExamBoard;
  description: string;
  subjectCount: number;
  topicCount: number;
  objectiveCount: number;
  difficultyLevel: "High School" | "Advanced Placement / A-Level" | "Undergraduate";
  iconName: string;
  subjects?: Subject[];
}

export interface CurriculumState {
  activeExamId: string;
  selectedTopic: Topic | null;
  searchQuery: string;
  expandedNodeIds: string[];
  isDrawerOpen: boolean;
  setActiveExam: (examId: string) => void;
  setSelectedTopic: (topic: Topic | null) => void;
  setSearchQuery: (query: string) => void;
  toggleNode: (nodeId: string) => void;
  expandAll: (nodeIds: string[]) => void;
  collapseAll: () => void;
  setIsDrawerOpen: (isOpen: boolean) => void;
}
