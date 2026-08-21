import type {
  PedagogicalMode,
  TutorSessionContext,
  SourceCitation,
} from "@/types/tutor";

export const SAMPLE_CITATIONS: Record<string, SourceCitation> = {
  mechanics: {
    id: "cite_mech_01",
    title: "Cambridge International AS & A Level Physics Coursebook",
    syllabusCode: "Cambridge 9702 §3.2",
    pageNumber: 84,
    snippet: "Conservation of Momentum: In any closed system where no external forces act, total linear momentum before collision equals total linear momentum after collision.",
  },
  waves: {
    id: "cite_waves_01",
    title: "Cambridge International AS & A Level Physics Coursebook",
    syllabusCode: "Cambridge 9702 §4.3",
    pageNumber: 118,
    snippet: "Doppler Effect: When a source emitting waves moves relative to an observer, the observed wavelength is compressed in front of the source and expanded behind.",
  },
  calculus: {
    id: "cite_calc_01",
    title: "Stewart Calculus: Early Transcendentals",
    syllabusCode: "AP Calc BC §3.4",
    pageNumber: 196,
    snippet: "The Chain Rule: If g is differentiable at x and f is differentiable at g(x), then F(x) = f(g(x)) has derivative F'(x) = f'(g(x)) * g'(x).",
  },
};

export const HINT_PROGRESSION: Record<number, { text: string; thoughts: string; citations: SourceCitation[] }> = {
  1: {
    thoughts: "Student requested Hint 1. Provide qualitative conceptual anchor without giving away algebraic formulas.",
    text: "Let's start by looking at the **governing physical principles**. Is energy or momentum conserved in this interaction? Consider what external forces (if any) are doing work on the system.",
    citations: [SAMPLE_CITATIONS.mechanics],
  },
  2: {
    thoughts: "Student requested Hint 2. Provide the algebraic formula relationship and identify variables.",
    text: "Here is the exact formula setup: Recall the relation for non-linear potential energy: $F(x) = -\\frac{dU}{dx}$. Once you take the derivative of $U(x)$, apply Newton's Second Law $F = ma$ to solve for acceleration $a(x)$.",
    citations: [SAMPLE_CITATIONS.mechanics],
  },
  3: {
    thoughts: "Student requested Hint 3. Provide the worked derivative step and isolate acceleration.",
    text: "Let's perform the derivative step-by-step: $\\frac{d}{dx}\\left[\\frac{1}{2}kx^2 + \\alpha x^4\\right] = kx + 4\\alpha x^3$. Therefore $F(x) = -(kx + 4\\alpha x^3)$. Dividing both sides by mass $m$ yields $a(x) = -\\frac{k}{m}x - \\frac{4\\alpha}{m}x^3$.",
    citations: [SAMPLE_CITATIONS.mechanics],
  },
};

export const socraticClient = {
  /**
   * Simulates streaming token chunks from the Socratic LLM gateway.
   */
  async *streamResponse(
    prompt: string,
    context?: TutorSessionContext | null,
    mode: PedagogicalMode = "socratic"
  ): AsyncGenerator<{ chunk: string; thoughts?: string; citations?: SourceCitation[] }> {
    let fullResponse = "";
    let thoughts = "Analyzing student response with pedagogical scaffolding.";
    let citations: SourceCitation[] = [SAMPLE_CITATIONS.mechanics];

    const lower = prompt.toLowerCase();

    if (mode === "teach_back") {
      thoughts = "Evaluating student's explanation against Cambridge syllabus rubric.";
      fullResponse =
        "Excellent explanation! You accurately identified that gravitational potential energy is converted into kinetic energy: $\\Delta K = -\\Delta U$. How would your reasoning change if air drag were significant?";
      citations = [SAMPLE_CITATIONS.mechanics];
    } else if (mode === "adversarial") {
      thoughts = "Identifying common student misconception regarding acceleration and velocity.";
      fullResponse =
        "Wait! A common misconception is assuming that when an object momentarily stops at the top of its trajectory ($v = 0$), its acceleration must also be zero. Is that true? Remember that gravity $g = 9.81\\text{ m/s}^2$ never turns off!";
      citations = [SAMPLE_CITATIONS.mechanics];
    } else if (lower.includes("doppler") || context?.topicTitle.includes("Doppler")) {
      thoughts = "Formulating Socratic question on Doppler frequency shift.";
      fullResponse =
        "Think about what happens to the wave crests emitted by the siren. Because the ambulance is chasing its own wavefronts, the wavelength $\\lambda' = \\frac{v - v_s}{f_s}$ gets compressed. What does this tell you about the observed frequency $f_o = \\frac{v}{\\lambda'}$?";
      citations = [SAMPLE_CITATIONS.waves];
    } else if (lower.includes("derivative") || lower.includes("calculus")) {
      thoughts = "Guiding student through the Chain Rule derivative.";
      fullResponse =
        "Let's break down the outer and inner functions. If $y = f(g(x))$, you take the derivative of the outer wrapper evaluated at $g(x)$, then multiply by the internal derivative $g'(x)$. What is the inner function in your problem?";
      citations = [SAMPLE_CITATIONS.calculus];
    } else {
      thoughts = "Providing Socratic probe on the active topic.";
      fullResponse = `Great question! In **${context?.topicTitle || "this topic"}**, let's first state what physical quantities are given. Can you write down the relationship between force $\\vec{F}$ and momentum $\\vec{p}$?`;
      citations = [SAMPLE_CITATIONS.mechanics];
    }

    const words = fullResponse.split(" ");
    for (let i = 0; i < words.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 15));
      yield {
        chunk: words[i] + (i === words.length - 1 ? "" : " "),
        thoughts: i === words.length - 1 ? thoughts : undefined,
        citations: i === words.length - 1 ? citations : undefined,
      };
    }
  },
};
