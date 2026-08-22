/**
 * TypeScript types for Student Analytics, Knowledge Tracing, and Error Bank.
 */

export type ErrorCategory = "conceptual" | "formula" | "calculation";

export interface TopicMasteryRecord {
  topicId: string;
  topicTitle: string;
  syllabusCode: string;
  accuracyPercentage: number;
  bktProbability: number; // 0.0 to 1.0 (Bayesian Knowledge Tracing estimate)
  totalAttempted: number;
  correctCount: number;
  masteryTier: "Mastered" | "Developing" | "Misconception";
  bloomLevel: "Recall" | "Application" | "Analysis" | "Evaluation";
}

export interface ErrorBankItem {
  id: string;
  topicId: string;
  topicTitle: string;
  syllabusCode: string;
  category: ErrorCategory;
  problemStemLatex: string;
  studentAnswer: string;
  correctAnswer: string;
  explanationLatex: string;
  misconceptionTag: string;
  misconceptionDetail: string;
  isResolved: boolean;
  dateRecorded: string;
}

export interface StudentAnalyticsSummary {
  studentId: string;
  studentName: string;
  overallReadinessPercentage: number; // P(Pass)
  estimatedGradeBand: string; // "A*" | "5 (Extremely Well Qualified)"
  totalSolved: number;
  overallAccuracy: number;
  streakDays: number;
  activeMisconceptionsCount: number;
  resolvedErrorsCount: number;
}

export interface AnalyticsState {
  summary: StudentAnalyticsSummary;
  topicMasteryRecords: TopicMasteryRecord[];
  errorBankItems: ErrorBankItem[];
  selectedCategoryFilter: string; // "all" | ErrorCategory
  selectedTopicFilter: string; // "all" | topicId

  // Actions
  setCategoryFilter: (category: string) => void;
  setTopicFilter: (topicId: string) => void;
  resolveErrorItem: (itemId: string) => void;
  resetAnalytics: () => void;
}
