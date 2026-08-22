/**
 * Types and models for the Interactive Exam Taking Player & Assessment Engine.
 */

export type QuestionType = "single_choice" | "multiple_choice" | "numeric_input";

export type QuestionDifficulty = "foundational" | "intermediate" | "advanced";

export interface QuestionOption {
  id: string; // "A" | "B" | "C" | "D"
  label: string; // "Option A"
  textLatex: string;
  isCorrect?: boolean;
}

export interface ExamQuestion {
  id: string;
  topicId: string;
  topicTitle: string;
  difficulty: QuestionDifficulty;
  type: QuestionType;
  stemLatex: string;
  options: QuestionOption[];
  correctOptionId: string;
  explanationLatex: string;
  hintLatex?: string;
  irtDifficulty?: number; // 0.0 to 1.0 IRT calibration
}

export interface ExamSession {
  id: string;
  examTemplateId: string;
  title: string;
  code: string;
  durationMinutes: number;
  questions: ExamQuestion[];
  startTimeMs?: number;
  endTimeMs?: number;
}

export interface TopicScoreBreakdown {
  topicId: string;
  topicTitle: string;
  totalQuestions: number;
  correctQuestions: number;
  percentage: number;
  masteryTier: "Mastered" | "Developing" | "Misconception";
}

export interface ExamScoreSummary {
  sessionId: string;
  examTitle: string;
  totalQuestions: number;
  answeredCount: number;
  correctCount: number;
  scorePercentage: number;
  timeSpentSeconds: number;
  topicBreakdowns: TopicScoreBreakdown[];
  completedAt: string;
}

export interface ExamPlayerState {
  session: ExamSession | null;
  currentQuestionIndex: number;
  answers: Record<string, string>; // questionId -> selectedOptionId
  flaggedQuestionIds: string[];
  timeRemainingSeconds: number;
  isSubmitted: boolean;
  isReviewModalOpen: boolean;
  scoreSummary: ExamScoreSummary | null;

  // Actions
  startSession: (session: ExamSession) => void;
  selectAnswer: (questionId: string, optionId: string) => void;
  clearAnswer: (questionId: string) => void;
  toggleFlag: (questionId: string) => void;
  nextQuestion: () => void;
  prevQuestion: () => void;
  goToQuestion: (index: number) => void;
  setIsReviewModalOpen: (isOpen: boolean) => void;
  submitExam: () => void;
  resetSession: () => void;
  tickTimer: () => void;
}
