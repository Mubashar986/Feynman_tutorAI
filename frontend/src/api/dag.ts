import type { DAGGraphData } from "@/types/dag";

export const SAMPLE_PHYSICS_DAG: DAGGraphData = {
  examTemplateId: "exam_cambridge_physics_9702",
  title: "Cambridge International A-Level Physics Prerequisite Graph",
  nodes: [
    {
      id: "topic_kinematics",
      topicTitle: "Kinematics & Motion Graphs",
      syllabusCode: "9702.1",
      x: 80,
      y: 100,
      accuracyPercentage: 92,
      bktProbability: 0.95,
      status: "mastered",
      bloomLevel: "Application",
      description:
        "1D and 2D projectile kinematics, velocity-time graphs, and uniform acceleration equations.",
      prerequisites: [],
      unlocks: ["topic_dynamics"],
    },
    {
      id: "topic_dynamics",
      topicTitle: "Newton's Laws & Dynamics",
      syllabusCode: "9702.2",
      x: 320,
      y: 100,
      accuracyPercentage: 85,
      bktProbability: 0.88,
      status: "mastered",
      bloomLevel: "Analysis",
      description:
        "Linear momentum conservation, Newton's three laws of motion, and vector force resolution.",
      prerequisites: ["topic_kinematics"],
      unlocks: ["topic_energy_power"],
    },
    {
      id: "topic_energy_power",
      topicTitle: "Work, Energy & Power",
      syllabusCode: "9702.3",
      x: 560,
      y: 100,
      accuracyPercentage: 78,
      bktProbability: 0.81,
      status: "developing",
      bloomLevel: "Analysis",
      description:
        "Conservative forces, kinetic vs potential energy conversion, and spatial gradient $F = -\\frac{dU}{dx}$.",
      prerequisites: ["topic_dynamics"],
      unlocks: ["topic_gravitation"],
      misconception: {
        tag: "Conservative Gradient Sign Error",
        detailLatex:
          "Omitting the negative sign in $F(x) = -\\frac{dU}{dx}$. Physical forces always push particles toward lower potential energy wells.",
        adversarialPrompt:
          "If a potential well is $U(x) = 5x^2$, which way does the force point when $x > 0$? Is it pushing outward or restoring toward the origin?",
      },
    },
    {
      id: "topic_gravitation",
      topicTitle: "Gravitational Fields & Orbits",
      syllabusCode: "9702.5",
      x: 800,
      y: 100,
      accuracyPercentage: 30,
      bktProbability: 0.25,
      status: "locked",
      bloomLevel: "Evaluation",
      description:
        "Universal gravitation $F = \\frac{GMm}{r^2}$, orbital mechanics, Kepler's third law, and escape velocity.",
      prerequisites: ["topic_energy_power"],
      unlocks: [],
    },
    {
      id: "topic_waves",
      topicTitle: "Wave Properties & Phase",
      syllabusCode: "9702.4",
      x: 80,
      y: 280,
      accuracyPercentage: 80,
      bktProbability: 0.84,
      status: "mastered",
      bloomLevel: "Recall",
      description:
        "Transverse and longitudinal oscillations, wavelength, frequency, wave speed $v = f\\lambda$, and phase difference.",
      prerequisites: [],
      unlocks: ["topic_superposition"],
    },
    {
      id: "topic_superposition",
      topicTitle: "Superposition & Interference",
      syllabusCode: "9702.6",
      x: 320,
      y: 280,
      accuracyPercentage: 45,
      bktProbability: 0.42,
      status: "misconception",
      bloomLevel: "Evaluation",
      description:
        "Constructive and destructive interference, Young's double-slit fringe spacing $x = \\frac{\\lambda D}{a}$, and diffraction gratings.",
      prerequisites: ["topic_waves"],
      unlocks: ["topic_doppler"],
      misconception: {
        tag: "Fringe Spacing Formula Inversion",
        detailLatex:
          "Inverting the geometric parameters in double slit diffraction: confusing slit spacing $a$ with screen distance $D$ in $x = \\frac{\\lambda D}{a}$.",
        adversarialPrompt:
          "If we bring the slits closer together (decreasing $a$), does the fringe pattern on the screen spread out or squeeze together? Explain why.",
      },
    },
    {
      id: "topic_doppler",
      topicTitle: "Doppler Effect in Waves",
      syllabusCode: "9702.7",
      x: 560,
      y: 280,
      accuracyPercentage: 65,
      bktProbability: 0.68,
      status: "developing",
      bloomLevel: "Application",
      description:
        "Observed frequency shifts for moving sound sources $f_o = f_s \\left(\\frac{v}{v \\pm v_s}\\right)$ and cosmological redshift.",
      prerequisites: ["topic_superposition"],
      unlocks: [],
      misconception: {
        tag: "Approaching vs Receding Frequency Shift",
        detailLatex:
          "Using $(v + v_s)$ instead of $(v - v_s)$ for approaching sources. Approaching sources compress wave crests, raising frequency.",
        adversarialPrompt:
          "When a racecar zooms towards you, why does the pitch sound higher before passing and immediately drop after passing?",
      },
    },
  ],
  edges: [
    { id: "e1", source: "topic_kinematics", target: "topic_dynamics", label: "Forces & Motion" },
    { id: "e2", source: "topic_dynamics", target: "topic_energy_power", label: "Work & Energy" },
    { id: "e3", source: "topic_energy_power", target: "topic_gravitation", label: "Orbital Mechanics" },
    { id: "e4", source: "topic_waves", target: "topic_superposition", label: "Interference" },
    { id: "e5", source: "topic_superposition", target: "topic_doppler", label: "Wave Shift" },
  ],
};

export const dagClient = {
  async getCurriculumDAG(): Promise<DAGGraphData> {
    return SAMPLE_PHYSICS_DAG;
  },
};
