/**
 * TypeScript types for Full Exam Simulation, Pacing Telemetry, and Calibrated Score Reports.
 */

export type SimulationMode = "proctored" | "guided";

export interface TopicWeight {
  topicTitle: string;
  syllabusCode: string;
  weightPercentage: number;
  questionCount: number;
}

export interface ExamBlueprint {
  id: string;
  title: string;
  examBoard: string;
  durationMinutes: number;
  totalQuestions: number;
  passingTargetScore: number;
  targetSecondsPerQuestion: number;
  description: string;
  topicWeights: TopicWeight[];
}

export interface PacingMetrics {
  averageSecondsPerQuestion: number;
  targetSecondsPerQuestion: number;
  totalTimeSpentSeconds: number;
  pacingStatus: "Optimal" | "On Target" | "Pacing Risk";
  fastestQuestionSeconds: number;
  slowestQuestionSeconds: number;
}

export interface TopicScoreBreakdown {
  topicTitle: string;
  syllabusCode: string;
  correctCount: number;
  totalQuestions: number;
  accuracyPercentage: number;
  masteryTier: "Mastered" | "Developing" | "Misconception";
  keyFormulaLatex: string;
}

export interface CalibratedScoreReport {
  id: string;
  examTitle: string;
  examBoard: string;
  mode: SimulationMode;
  rawScore: number;
  totalQuestions: number;
  percentage: number;
  predictedGradeBand: string; // e.g. "A*" or "Score 5"
  confidenceInterval: string; // e.g. "88% - 96%"
  pacing: PacingMetrics;
  topicBreakdowns: TopicScoreBreakdown[];
  completionDate: string;
}

export interface SimulationState {
  activeBlueprint: ExamBlueprint;
  simulationMode: SimulationMode;
  activeScoreReport: CalibratedScoreReport | null;
  simulationHistory: CalibratedScoreReport[];

  // Actions
  setBlueprint: (blueprint: ExamBlueprint) => void;
  setSimulationMode: (mode: SimulationMode) => void;
  setScoreReport: (report: CalibratedScoreReport | null) => void;
  resetSimulation: () => void;
}
