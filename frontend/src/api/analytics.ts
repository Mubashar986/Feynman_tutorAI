import type {
  StudentAnalyticsSummary,
  TopicMasteryRecord,
  ErrorBankItem,
} from "@/types/analytics";

export const DEFAULT_STUDENT_SUMMARY: StudentAnalyticsSummary = {
  studentId: "student_alex",
  studentName: "Alex Rivera",
  overallReadinessPercentage: 88,
  estimatedGradeBand: "A* (Predicted Score > 90%)",
  totalSolved: 42,
  overallAccuracy: 83,
  streakDays: 5,
  activeMisconceptionsCount: 3,
  resolvedErrorsCount: 9,
};

export const DEFAULT_TOPIC_MASTERY_RECORDS: TopicMasteryRecord[] = [
  {
    topicId: "topic_kinematics",
    topicTitle: "Kinematics & Motion Graphs",
    syllabusCode: "9702.1",
    accuracyPercentage: 92,
    bktProbability: 0.95,
    totalAttempted: 12,
    correctCount: 11,
    masteryTier: "Mastered",
    bloomLevel: "Application",
  },
  {
    topicId: "topic_energy_power",
    topicTitle: "Work, Energy & Power",
    syllabusCode: "9702.2",
    accuracyPercentage: 85,
    bktProbability: 0.88,
    totalAttempted: 10,
    correctCount: 8,
    masteryTier: "Mastered",
    bloomLevel: "Analysis",
  },
  {
    topicId: "topic_gravitation",
    topicTitle: "Gravitational Fields & Orbits",
    syllabusCode: "9702.5",
    accuracyPercentage: 78,
    bktProbability: 0.81,
    totalAttempted: 8,
    correctCount: 6,
    masteryTier: "Developing",
    bloomLevel: "Analysis",
  },
  {
    topicId: "topic_doppler",
    topicTitle: "Doppler Effect in Sound & Light",
    syllabusCode: "9702.4",
    accuracyPercentage: 65,
    bktProbability: 0.68,
    totalAttempted: 6,
    correctCount: 4,
    masteryTier: "Developing",
    bloomLevel: "Application",
  },
  {
    topicId: "topic_superposition",
    topicTitle: "Superposition & Interference",
    syllabusCode: "9702.3",
    accuracyPercentage: 45,
    bktProbability: 0.42,
    totalAttempted: 6,
    correctCount: 3,
    masteryTier: "Misconception",
    bloomLevel: "Evaluation",
  },
];

export const DEFAULT_ERROR_BANK_ITEMS: ErrorBankItem[] = [
  {
    id: "err_doppler_01",
    topicId: "topic_doppler",
    topicTitle: "Doppler Effect in Sound & Light",
    syllabusCode: "9702.4",
    category: "conceptual",
    problemStemLatex:
      "A siren emitting frequency $f_s = 600\\text{ Hz}$ approaches a stationary listener at $v_s = 34\\text{ m/s}$. Speed of sound is $v = 340\\text{ m/s}$. What is the observed frequency $f_o$?",
    studentAnswer: "B: 545 Hz (Used + instead of - in denominator)",
    correctAnswer: "A: 667 Hz (f_o = f_s * [v / (v - v_s)])",
    explanationLatex:
      "Because the source is chasing its wavefronts, the wavelength is compressed: $\\lambda' = \\frac{v - v_s}{f_s}$. Hence observed frequency increases: $f_o = f_s \\left(\\frac{v}{v - v_s}\\right) = 667\\text{ Hz}$.",
    misconceptionTag: "Approaching Source Frequency Dilation",
    misconceptionDetail:
      "Conflating receding source formula with approaching source. For an approaching source, the denominator is $(v - v_s)$, yielding a higher frequency.",
    isResolved: false,
    dateRecorded: "2026-08-21T18:30:00.000Z",
  },
  {
    id: "err_superposition_01",
    topicId: "topic_superposition",
    topicTitle: "Superposition & Interference",
    syllabusCode: "9702.3",
    category: "formula",
    problemStemLatex:
      "In a Young's double slit setup with slit spacing $a = 0.20\\text{ mm}$, screen distance $D = 2.0\\text{ m}$, and wavelength $\\lambda = 500\\text{ nm}$, find the fringe separation $x$.",
    studentAnswer: "B: x = 8.0 mm (Inverted formula a*D / lambda)",
    correctAnswer: "A: x = 5.0 mm (x = lambda * D / a)",
    explanationLatex:
      "Fringe separation is directly proportional to wavelength and screen distance, inversely proportional to slit width: $x = \\frac{\\lambda D}{a} = \\frac{(500\\times 10^{-9})(2.0)}{0.20\\times 10^{-3}} = 5.0\\text{ mm}$.",
    misconceptionTag: "Fringe Width Geometric Inversion",
    misconceptionDetail:
      "Inverting geometric parameters in wave interference equations. Narrower slit spacing increases angular spread, making fringes wider.",
    isResolved: false,
    dateRecorded: "2026-08-21T18:45:00.000Z",
  },
  {
    id: "err_energy_01",
    topicId: "topic_energy_power",
    topicTitle: "Work, Energy & Power",
    syllabusCode: "9702.2",
    category: "calculation",
    problemStemLatex:
      "Find acceleration $a(x)$ for a particle of mass $m$ in potential field $U(x) = \\frac{1}{2} k x^2 + \\alpha x^4$.",
    studentAnswer: "C: a(x) = +k/m x + 4alpha/m x^3 (Missing negative sign)",
    correctAnswer: "A: a(x) = -k/m x - 4alpha/m x^3",
    explanationLatex:
      "Conservative force is the negative spatial derivative of potential energy: $F(x) = -\\frac{dU}{dx} = -(kx + 4\\alpha x^3)$. By $F = ma$, $a(x) = -\\frac{k}{m}x - \\frac{4\\alpha}{m}x^3$.",
    misconceptionTag: "Conservative Gradient Sign Drop",
    misconceptionDetail:
      "Omitting the negative gradient in $F = -\\nabla U$. Forces point in the direction of decreasing potential energy.",
    isResolved: false,
    dateRecorded: "2026-08-21T19:10:00.000Z",
  },
];

export const analyticsClient = {
  async getStudentAnalytics(): Promise<{
    summary: StudentAnalyticsSummary;
    topics: TopicMasteryRecord[];
    errors: ErrorBankItem[];
  }> {
    return {
      summary: DEFAULT_STUDENT_SUMMARY,
      topics: DEFAULT_TOPIC_MASTERY_RECORDS,
      errors: DEFAULT_ERROR_BANK_ITEMS,
    };
  },
};
