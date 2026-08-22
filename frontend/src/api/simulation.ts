import type { ExamBlueprint, CalibratedScoreReport } from "@/types/simulation";

export const EXAM_BLUEPRINTS: ExamBlueprint[] = [
  {
    id: "blueprint_cambridge_physics_9702",
    title: "Cambridge International A-Level Physics (9702) Paper 1",
    examBoard: "Cambridge Assessment International Education",
    durationMinutes: 60,
    totalQuestions: 40,
    passingTargetScore: 32,
    targetSecondsPerQuestion: 90,
    description:
      "Official 40-question multiple-choice diagnostic paper covering mechanics, oscillations, waves, electricity, and particle physics.",
    topicWeights: [
      {
        topicTitle: "Classical Mechanics & Kinematics",
        syllabusCode: "9702.1 - 9702.3",
        weightPercentage: 40,
        questionCount: 16,
      },
      {
        topicTitle: "Waves, Superposition & Doppler",
        syllabusCode: "9702.4 - 9702.7",
        weightPercentage: 30,
        questionCount: 12,
      },
      {
        topicTitle: "Electricity, Fields & Modern Physics",
        syllabusCode: "9702.8 - 9702.11",
        weightPercentage: 30,
        questionCount: 12,
      },
    ],
  },
  {
    id: "blueprint_ap_calc_bc",
    title: "AP Calculus BC Full Simulation Exam (Section I)",
    examBoard: "College Board",
    durationMinutes: 105,
    totalQuestions: 45,
    passingTargetScore: 30,
    targetSecondsPerQuestion: 140,
    description:
      "Comprehensive 45-question diagnostic covering limits, derivatives, integrals, Taylor/Maclaurin series, and parametric equations.",
    topicWeights: [
      {
        topicTitle: "Differential Calculus & Applications",
        syllabusCode: "AP-BC-1 - AP-BC-3",
        weightPercentage: 35,
        questionCount: 16,
      },
      {
        topicTitle: "Integral Calculus & Differential Equations",
        syllabusCode: "AP-BC-4 - AP-BC-6",
        weightPercentage: 35,
        questionCount: 16,
      },
      {
        topicTitle: "Infinite Series, Sequences & Polar",
        syllabusCode: "AP-BC-7 - AP-BC-10",
        weightPercentage: 30,
        questionCount: 13,
      },
    ],
  },
];

export const SAMPLE_PHYSICS_SCORE_REPORT: CalibratedScoreReport = {
  id: "rep_cambridge_mock_01",
  examTitle: "Cambridge International A-Level Physics (9702) Paper 1",
  examBoard: "Cambridge Assessment International Education",
  mode: "proctored",
  rawScore: 35,
  totalQuestions: 40,
  percentage: 87.5,
  predictedGradeBand: "A*",
  confidenceInterval: "84% - 92%",
  pacing: {
    averageSecondsPerQuestion: 68,
    targetSecondsPerQuestion: 90,
    totalTimeSpentSeconds: 2720,
    pacingStatus: "Optimal",
    fastestQuestionSeconds: 24,
    slowestQuestionSeconds: 112,
  },
  topicBreakdowns: [
    {
      topicTitle: "Classical Mechanics & Kinematics",
      syllabusCode: "9702.1 - 9702.3",
      correctCount: 15,
      totalQuestions: 16,
      accuracyPercentage: 93.8,
      masteryTier: "Mastered",
      keyFormulaLatex: "v^2 = u^2 + 2as, \\quad F = -\\frac{dU}{dx}",
    },
    {
      topicTitle: "Waves, Superposition & Doppler",
      syllabusCode: "9702.4 - 9702.7",
      correctCount: 10,
      totalQuestions: 12,
      accuracyPercentage: 83.3,
      masteryTier: "Mastered",
      keyFormulaLatex: "x = \\frac{\\lambda D}{a}, \\quad f_o = f_s\\left(\\frac{v}{v - v_s}\\right)",
    },
    {
      topicTitle: "Electricity, Fields & Modern Physics",
      syllabusCode: "9702.8 - 9702.11",
      correctCount: 10,
      totalQuestions: 12,
      accuracyPercentage: 83.3,
      masteryTier: "Developing",
      keyFormulaLatex: "E = \\frac{V}{d}, \\quad P = I^2R = \\frac{V^2}{R}",
    },
  ],
  completionDate: "2026-08-22",
};

export const simulationClient = {
  async getBlueprints(): Promise<ExamBlueprint[]> {
    return EXAM_BLUEPRINTS;
  },
  async getSampleReport(): Promise<CalibratedScoreReport> {
    return SAMPLE_PHYSICS_SCORE_REPORT;
  },
};
