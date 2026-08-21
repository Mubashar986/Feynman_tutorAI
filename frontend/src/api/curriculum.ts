import type { ExamTemplate, Subject } from "@/types/curriculum";

export const EXAM_CATALOG: ExamTemplate[] = [
  {
    id: "exam_cambridge_physics_9702",
    title: "Cambridge International A-Level Physics",
    code: "9702",
    board: "Cambridge International",
    description: "Covers classical mechanics, wave phenomena, fields, quantum physics, and nuclear thermodynamics for university STEM admissions.",
    subjectCount: 3,
    topicCount: 7,
    objectiveCount: 16,
    difficultyLevel: "Advanced Placement / A-Level",
    iconName: "Atom",
  },
  {
    id: "exam_ap_calculus_bc",
    title: "AP Calculus BC",
    code: "AP-CALC-BC",
    board: "College Board",
    description: "Comprehensive single-variable calculus including derivatives, integration techniques, polar/vector coordinates, and infinite series.",
    subjectCount: 3,
    topicCount: 7,
    objectiveCount: 15,
    difficultyLevel: "Advanced Placement / A-Level",
    iconName: "Binary",
  },
  {
    id: "exam_sat_math",
    title: "Digital SAT Mathematics",
    code: "SAT-MATH",
    board: "College Board",
    description: "Core algebraic fluency, advanced polynomial equations, geometric modeling, and data analysis for college entrance.",
    subjectCount: 3,
    topicCount: 6,
    objectiveCount: 12,
    difficultyLevel: "High School",
    iconName: "Calculator",
  },
];

export const CAMBRIDGE_PHYSICS_SUBJECTS: Subject[] = [
  {
    id: "subj_mechanics",
    examTemplateId: "exam_cambridge_physics_9702",
    title: "1. Classical Mechanics & Kinematics",
    order: 1,
    description: "Motion in one and two dimensions, forces, conservation of momentum, and mechanical energy.",
    topics: [
      {
        id: "topic_kinematics",
        subjectId: "subj_mechanics",
        title: "Kinematics & Motion Graphs",
        order: 1,
        difficulty: "foundational",
        estimatedHours: 6,
        description: "Equations of uniformly accelerated motion and projectile trajectory analysis.",
        prerequisites: [],
        objectives: [
          {
            id: "obj_kin_1",
            code: "9702.1.1",
            description: "Derive and apply the equations of motion for constant acceleration.",
            formulaLatex: "v = u + at, \\quad s = ut + \\frac{1}{2}at^2, \\quad v^2 = u^2 + 2as",
            bloomLevel: "Apply",
          },
          {
            id: "obj_kin_2",
            code: "9702.1.2",
            description: "Analyze displacement-time and velocity-time graphs for non-uniform motion.",
            formulaLatex: "v = \\frac{ds}{dt}, \\quad a = \\frac{dv}{dt}",
            bloomLevel: "Analyze",
          },
        ],
      },
      {
        id: "topic_dynamics",
        subjectId: "subj_mechanics",
        title: "Newton's Laws & Linear Momentum",
        order: 2,
        difficulty: "intermediate",
        estimatedHours: 8,
        description: "Net force, impulse, and conservation of linear momentum in 1D and 2D collisions.",
        prerequisites: [
          {
            topicId: "topic_dynamics",
            prerequisiteTopicId: "topic_kinematics",
            prerequisiteTopicTitle: "Kinematics & Motion Graphs",
            isMandatory: true,
          },
        ],
        objectives: [
          {
            id: "obj_dyn_1",
            code: "9702.2.1",
            description: "State Newton's second law in terms of rate of change of momentum.",
            formulaLatex: "F_{net} = \\frac{dp}{dt} = m \\frac{dv}{dt}",
            bloomLevel: "Understand",
          },
          {
            id: "obj_dyn_2",
            code: "9702.2.2",
            description: "Apply conservation of linear momentum to elastic and inelastic collisions.",
            formulaLatex: "m_1 u_1 + m_2 u_2 = m_1 v_1 + m_2 v_2",
            bloomLevel: "Apply",
          },
        ],
      },
      {
        id: "topic_energy_power",
        subjectId: "subj_mechanics",
        title: "Work, Energy & Power",
        order: 3,
        difficulty: "intermediate",
        estimatedHours: 6,
        description: "Mechanical work done by variable forces and efficiency calculations.",
        prerequisites: [
          {
            topicId: "topic_energy_power",
            prerequisiteTopicId: "topic_dynamics",
            prerequisiteTopicTitle: "Newton's Laws & Linear Momentum",
            isMandatory: true,
          },
        ],
        objectives: [
          {
            id: "obj_en_1",
            code: "9702.3.1",
            description: "Calculate work done by a constant or variable force.",
            formulaLatex: "W = \\int \\vec{F} \\cdot d\\vec{r} = F s \\cos(\\theta)",
            bloomLevel: "Apply",
          },
          {
            id: "obj_en_2",
            code: "9702.3.2",
            description: "Calculate mechanical power delivered in continuous motion.",
            formulaLatex: "P = \\frac{dW}{dt} = F v",
            bloomLevel: "Apply",
          },
        ],
      },
    ],
  },
  {
    id: "subj_waves",
    examTemplateId: "exam_cambridge_physics_9702",
    title: "2. Waves & Superposition",
    order: 2,
    description: "Wave propagation, transverse and longitudinal waves, Doppler shift, and diffraction patterns.",
    topics: [
      {
        id: "topic_wave_properties",
        subjectId: "subj_waves",
        title: "Progressive Waves & Polarisation",
        order: 1,
        difficulty: "foundational",
        estimatedHours: 5,
        description: "Wavelength, frequency, phase difference, and Malus's Law.",
        prerequisites: [],
        objectives: [
          {
            id: "obj_wv_1",
            code: "9702.4.1",
            description: "Recall and apply the wave equation relating speed, frequency, and wavelength.",
            formulaLatex: "v = f \\lambda = \\frac{\\lambda}{T}",
            bloomLevel: "Apply",
          },
          {
            id: "obj_wv_2",
            code: "9702.4.2",
            description: "Explain polarization and calculate transmitted intensity with Malus's Law.",
            formulaLatex: "I = I_0 \\cos^2(\\theta)",
            bloomLevel: "Analyze",
          },
        ],
      },
      {
        id: "topic_doppler",
        subjectId: "subj_waves",
        title: "Doppler Effect in Sound & Light",
        order: 2,
        difficulty: "intermediate",
        estimatedHours: 4,
        description: "Observed frequency shifts caused by moving sources and observers.",
        prerequisites: [
          {
            topicId: "topic_doppler",
            prerequisiteTopicId: "topic_wave_properties",
            prerequisiteTopicTitle: "Progressive Waves & Polarisation",
            isMandatory: true,
          },
        ],
        objectives: [
          {
            id: "obj_dop_1",
            code: "9702.5.1",
            description: "Calculate observed frequency for a moving source.",
            formulaLatex: "f_o = f_s \\left( \\frac{v}{v \\pm v_s} \\right)",
            bloomLevel: "Apply",
          },
        ],
      },
      {
        id: "topic_superposition",
        subjectId: "subj_waves",
        title: "Superposition & Interference",
        order: 3,
        difficulty: "advanced",
        estimatedHours: 8,
        description: "Young's double-slit experiment and diffraction gratings.",
        prerequisites: [
          {
            topicId: "topic_superposition",
            prerequisiteTopicId: "topic_wave_properties",
            prerequisiteTopicTitle: "Progressive Waves & Polarisation",
            isMandatory: true,
          },
        ],
        objectives: [
          {
            id: "obj_sup_1",
            code: "9702.6.1",
            description: "Determine fringe separation in double-slit interference.",
            formulaLatex: "x = \\frac{\\lambda D}{a}",
            bloomLevel: "Apply",
          },
          {
            id: "obj_sup_2",
            code: "9702.6.2",
            description: "Calculate spectral maxima from a diffraction grating.",
            formulaLatex: "d \\sin(\\theta) = n \\lambda",
            bloomLevel: "Analyze",
          },
        ],
      },
    ],
  },
  {
    id: "subj_fields",
    examTemplateId: "exam_cambridge_physics_9702",
    title: "3. Gravitational & Electric Fields",
    order: 3,
    description: "Field theory, inverse-square laws, potentials, and satellite orbital mechanics.",
    topics: [
      {
        id: "topic_gravitation",
        subjectId: "subj_fields",
        title: "Gravitational Fields & Orbits",
        order: 1,
        difficulty: "advanced",
        estimatedHours: 8,
        description: "Newton's law of universal gravitation, gravitational potential, and orbital velocity.",
        prerequisites: [
          {
            topicId: "topic_gravitation",
            prerequisiteTopicId: "topic_dynamics",
            prerequisiteTopicTitle: "Newton's Laws & Linear Momentum",
            isMandatory: true,
          },
        ],
        objectives: [
          {
            id: "obj_grv_1",
            code: "9702.7.1",
            description: "Calculate gravitational force and potential between point masses.",
            formulaLatex: "F_g = G \\frac{M m}{r^2}, \\quad \\phi = -\\frac{G M}{r}",
            bloomLevel: "Analyze",
          },
          {
            id: "obj_grv_2",
            code: "9702.7.2",
            description: "Derive circular orbital speed and Kepler's Third Law.",
            formulaLatex: "v_{orbit} = \\sqrt{\\frac{G M}{r}}, \\quad T^2 = \\frac{4\\pi^2}{GM} r^3",
            bloomLevel: "Create",
          },
        ],
      },
    ],
  },
];

export const AP_CALCULUS_SUBJECTS: Subject[] = [
  {
    id: "subj_calc_derivatives",
    examTemplateId: "exam_ap_calculus_bc",
    title: "1. Differential Calculus & Applications",
    order: 1,
    description: "Limits, continuity, derivative rules, Mean Value Theorem, and related rates.",
    topics: [
      {
        id: "topic_calc_rules",
        subjectId: "subj_calc_derivatives",
        title: "Advanced Differentiation Rules",
        order: 1,
        difficulty: "foundational",
        estimatedHours: 6,
        description: "Chain rule, implicit differentiation, and inverse trigonometric derivatives.",
        prerequisites: [],
        objectives: [
          {
            id: "obj_diff_1",
            code: "CALC.1.1",
            description: "Apply Chain Rule to composite functions.",
            formulaLatex: "\\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)",
            bloomLevel: "Apply",
          },
        ],
      },
    ],
  },
  {
    id: "subj_calc_series",
    examTemplateId: "exam_ap_calculus_bc",
    title: "2. Infinite Sequences & Series",
    order: 2,
    description: "Convergence tests, power series, Taylor and Maclaurin polynomial expansions.",
    topics: [
      {
        id: "topic_taylor_series",
        subjectId: "subj_calc_series",
        title: "Taylor & Maclaurin Series",
        order: 1,
        difficulty: "advanced",
        estimatedHours: 10,
        description: "Derivation and Lagrange error bounds for polynomial approximations.",
        prerequisites: [
          {
            topicId: "topic_taylor_series",
            prerequisiteTopicId: "topic_calc_rules",
            prerequisiteTopicTitle: "Advanced Differentiation Rules",
            isMandatory: true,
          },
        ],
        objectives: [
          {
            id: "obj_ser_1",
            code: "CALC.2.1",
            description: "Construct Taylor polynomial centered at x = a.",
            formulaLatex: "P_n(x) = \\sum_{k=0}^{n} \\frac{f^{(k)}(a)}{k!} (x - a)^k",
            bloomLevel: "Create",
          },
        ],
      },
    ],
  },
];

export const curriculumClient = {
  /**
   * Retrieves all available exam templates.
   */
  async getExamTemplates(): Promise<ExamTemplate[]> {
    return EXAM_CATALOG;
  },

  /**
   * Retrieves full syllabus hierarchy for a given exam.
   */
  async getSyllabusTree(examId: string): Promise<Subject[]> {
    if (examId === "exam_ap_calculus_bc") {
      return AP_CALCULUS_SUBJECTS;
    }
    // Default to Cambridge Physics
    return CAMBRIDGE_PHYSICS_SUBJECTS;
  },
};
