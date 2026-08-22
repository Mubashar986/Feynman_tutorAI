import type { ExamSession, ExamScoreSummary, TopicScoreBreakdown, ExamQuestion } from "@/types/exam";

export const SAMPLE_PHYSICS_EXAM: ExamSession = {
  id: "session_physics_9702_diagnostic",
  examTemplateId: "exam_cambridge_physics_9702",
  title: "Cambridge A-Level Physics Diagnostic Exam",
  code: "9702/01",
  durationMinutes: 15,
  questions: [
    {
      id: "q_phys_01",
      topicId: "topic_kinematics",
      topicTitle: "Kinematics & Motion Graphs",
      difficulty: "intermediate",
      type: "single_choice",
      stemLatex: "A particle is launched from ground level with initial velocity $u = 20\\text{ m/s}$ at an angle $\\theta = 30^\\circ$ above the horizontal. Neglecting air resistance, what is the horizontal range $R$ of the projectile? (Take $g = 9.81\\text{ m/s}^2$)",
      options: [
        { id: "A", label: "Option A", textLatex: "R = \\frac{u^2 \\sin(2\\theta)}{g} \\approx 35.3\\text{ m}" },
        { id: "B", label: "Option B", textLatex: "R = \\frac{u^2 \\sin^2(\\theta)}{2g} \\approx 5.1\\text{ m}" },
        { id: "C", label: "Option C", textLatex: "R = \\frac{2u \\sin(\\theta)}{g} \\approx 2.0\\text{ m}" },
        { id: "D", label: "Option D", textLatex: "R = \\frac{u^2 \\cos(2\\theta)}{g} \\approx 20.4\\text{ m}" },
      ],
      correctOptionId: "A",
      explanationLatex: "The horizontal range formula is derived by combining time of flight $T = \\frac{2u\\sin(\\theta)}{g}$ with constant horizontal velocity $u_x = u\\cos(\\theta)$, yielding $R = u_x T = \\frac{u^2 \\sin(2\\theta)}{g} = \\frac{400 \\sin(60^\\circ)}{9.81} \\approx 35.3\\text{ m}$.",
      hintLatex: "Use the double angle identity $2\\sin(\\theta)\\cos(\\theta) = \\sin(2\\theta)$.",
      irtDifficulty: 0.55,
    },
    {
      id: "q_phys_02",
      topicId: "topic_energy_power",
      topicTitle: "Work, Energy & Power",
      difficulty: "advanced",
      type: "single_choice",
      stemLatex: "A conservative particle moves in a 1D potential field described by $U(x) = \\frac{1}{2} k x^2 + \\alpha x^4$. Which expression gives the acceleration $a(x)$ of the particle with mass $m$?",
      options: [
        { id: "A", label: "Option A", textLatex: "a(x) = -\\frac{k}{m}x - \\frac{4\\alpha}{m}x^3" },
        { id: "B", label: "Option B", textLatex: "a(x) = -\\frac{k}{m}x - \\frac{\\alpha}{m}x^3" },
        { id: "C", label: "Option C", textLatex: "a(x) = \\frac{k}{m}x + \\frac{4\\alpha}{m}x^3" },
        { id: "D", label: "Option D", textLatex: "a(x) = -kx - 4\\alpha x^3" },
      ],
      correctOptionId: "A",
      explanationLatex: "The conservative force is the negative derivative of potential energy: $F(x) = -\\frac{dU}{dx} = -(kx + 4\\alpha x^3)$. From Newton's Second Law $F = ma$, acceleration is $a(x) = \\frac{F(x)}{m} = -\\frac{k}{m}x - \\frac{4\\alpha}{m}x^3$.",
      hintLatex: "Remember $F = -\\frac{dU}{dx}$ and $a = \\frac{F}{m}$.",
      irtDifficulty: 0.75,
    },
    {
      id: "q_phys_03",
      topicId: "topic_doppler",
      topicTitle: "Doppler Effect in Sound & Light",
      difficulty: "intermediate",
      type: "single_choice",
      stemLatex: "A siren emitting a steady frequency $f_s = 600\\text{ Hz}$ moves directly towards a stationary observer at speed $v_s = 34\\text{ m/s}$. If the speed of sound in air is $v = 340\\text{ m/s}$, what frequency $f_o$ does the observer perceive?",
      options: [
        { id: "A", label: "Option A", textLatex: "f_o = f_s \\left( \\frac{v}{v - v_s} \\right) = 667\\text{ Hz}" },
        { id: "B", label: "Option B", textLatex: "f_o = f_s \\left( \\frac{v}{v + v_s} \\right) = 545\\text{ Hz}" },
        { id: "C", label: "Option C", textLatex: "f_o = f_s \\left( 1 + \\frac{v_s}{v} \\right) = 660\\text{ Hz}" },
        { id: "D", label: "Option D", textLatex: "f_o = 600\\text{ Hz}" },
      ],
      correctOptionId: "A",
      explanationLatex: "When the sound source approaches a stationary observer, the observed wave fronts are compressed: $f_o = f_s \\left(\\frac{v}{v - v_s}\\right) = 600 \\times \\left(\\frac{340}{340 - 34}\\right) = 600 \\times \\frac{340}{306} \\approx 667\\text{ Hz}$.",
      hintLatex: "The observed frequency increases as the source moves closer.",
      irtDifficulty: 0.60,
    },
    {
      id: "q_phys_04",
      topicId: "topic_superposition",
      topicTitle: "Superposition & Interference",
      difficulty: "intermediate",
      type: "single_choice",
      stemLatex: "In a Young's double-slit experiment, monochromatic light of wavelength $\\lambda = 500\\text{ nm}$ illuminates two slits separated by distance $a = 0.20\\text{ mm}$. The interference pattern is viewed on a screen at distance $D = 2.0\\text{ m}$. What is the fringe separation $x$?",
      options: [
        { id: "A", label: "Option A", textLatex: "x = \\frac{\\lambda D}{a} = 5.0\\text{ mm}" },
        { id: "B", label: "Option B", textLatex: "x = \\frac{a D}{\\lambda} = 8.0\\text{ mm}" },
        { id: "C", label: "Option C", textLatex: "x = \\frac{\\lambda a}{D} = 0.05\\text{ mm}" },
        { id: "D", label: "Option D", textLatex: "x = 2.5\\text{ mm}" },
      ],
      correctOptionId: "A",
      explanationLatex: "Double-slit fringe separation is given by $x = \\frac{\\lambda D}{a}$. Substituting values: $x = \\frac{(500 \\times 10^{-9}\\text{ m})(2.0\\text{ m})}{0.20 \\times 10^{-3}\\text{ m}} = 5.0 \\times 10^{-3}\\text{ m} = 5.0\\text{ mm}$.",
      hintLatex: "Keep all measurements in standard SI meters before computing.",
      irtDifficulty: 0.50,
    },
    {
      id: "q_phys_05",
      topicId: "topic_gravitation",
      topicTitle: "Gravitational Fields & Orbits",
      difficulty: "advanced",
      type: "single_choice",
      stemLatex: "A satellite of mass $m$ is in a circular orbit of radius $r$ around a planet of mass $M$. What is the satellite's total mechanical energy $E_{tot}$ in terms of gravitational constant $G$?",
      options: [
        { id: "A", label: "Option A", textLatex: "E_{tot} = -\\frac{G M m}{2r}" },
        { id: "B", label: "Option B", textLatex: "E_{tot} = -\\frac{G M m}{r}" },
        { id: "C", label: "Option C", textLatex: "E_{tot} = +\\frac{G M m}{2r}" },
        { id: "D", label: "Option D", textLatex: "E_{tot} = 0" },
      ],
      correctOptionId: "A",
      explanationLatex: "Kinetic energy in circular orbit is $E_k = \\frac{1}{2} m v^2 = \\frac{G M m}{2r}$. Potential energy is $E_p = -\\frac{G M m}{r}$. Total mechanical energy is $E_{tot} = E_k + E_p = \\frac{G M m}{2r} - \\frac{G M m}{r} = -\\frac{G M m}{2r}$.",
      hintLatex: "In circular gravitational orbits, $E_k = -\\frac{1}{2} E_p$.",
      irtDifficulty: 0.80,
    },
  ],
};

export const examClient = {
  /**
   * Loads the diagnostic exam session for the active blueprint.
   */
  async getExamSession(examTemplateId: string): Promise<ExamSession> {
    // Return sample physics diagnostic session by default
    return {
      ...SAMPLE_PHYSICS_EXAM,
      examTemplateId,
    };
  },

  /**
   * Grades student answers and aggregates topic mastery metrics.
   */
  gradeExamSession(
    session: ExamSession,
    answers: Record<string, string>,
    timeSpentSeconds: number
  ): ExamScoreSummary {
    let correctCount = 0;
    const answeredCount = Object.keys(answers).length;

    // Grouping by topic
    const topicMap: Record<
      string,
      { title: string; total: number; correct: number }
    > = {};

    session.questions.forEach((q: ExamQuestion) => {
      if (!topicMap[q.topicId]) {
        topicMap[q.topicId] = { title: q.topicTitle, total: 0, correct: 0 };
      }
      topicMap[q.topicId].total += 1;

      const studentAns = answers[q.id];
      if (studentAns === q.correctOptionId) {
        correctCount += 1;
        topicMap[q.topicId].correct += 1;
      }
    });

    const scorePercentage = Math.round(
      (correctCount / session.questions.length) * 100
    );

    const topicBreakdowns: TopicScoreBreakdown[] = Object.entries(topicMap).map(
      ([topicId, stats]) => {
        const pct = Math.round((stats.correct / stats.total) * 100);
        let tier: "Mastered" | "Developing" | "Misconception" = "Developing";
        if (pct >= 80) tier = "Mastered";
        else if (pct < 50) tier = "Misconception";

        return {
          topicId,
          topicTitle: stats.title,
          totalQuestions: stats.total,
          correctQuestions: stats.correct,
          percentage: pct,
          masteryTier: tier,
        };
      }
    );

    return {
      sessionId: session.id,
      examTitle: session.title,
      totalQuestions: session.questions.length,
      answeredCount,
      correctCount,
      scorePercentage,
      timeSpentSeconds,
      topicBreakdowns,
      completedAt: new Date().toISOString(),
    };
  },
};
