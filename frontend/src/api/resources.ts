import type { CurriculumDocument } from "@/types/resource";

export const SAMPLE_CURRICULUM_DOCUMENTS: CurriculumDocument[] = [
  {
    id: "doc_cambridge_physics_9702",
    title: "Cambridge International AS & A Level Physics Coursebook",
    examBoard: "Cambridge Assessment International Education",
    type: "coursebook",
    author: "David Sang, Graham Jones, Richard Woodside",
    edition: "3rd Edition (Official Curriculum Endorsed)",
    totalPages: 540,
    description:
      "Comprehensive textbook covering all syllabus learning objectives for Cambridge International AS & A Level Physics (9702).",
    sections: [
      {
        id: "sec_kinematics_equations",
        sectionNumber: "1.1",
        title: "Kinematics & Constant Acceleration Equations",
        syllabusCode: "9702.1.1",
        pageNumber: 14,
        content:
          "For an object moving in a straight line with uniform acceleration $a$, the relationships between initial velocity $u$, final velocity $v$, displacement $s$, and elapsed time $t$ are given by the standard kinematic equations. These equations are derived under the strict boundary condition that acceleration remains constant throughout the interval of observation.",
        keyFormulas: [
          "v = u + at",
          "s = ut + \\frac{1}{2}at^2",
          "v^2 = u^2 + 2as",
          "s = \\frac{(u + v)}{2}t",
        ],
        verifiedCitationSnippet:
          "These equations are derived under the strict boundary condition that acceleration remains constant throughout the interval of observation.",
      },
      {
        id: "sec_dynamics_newton",
        sectionNumber: "2.1",
        title: "Newton's Laws of Motion & Momentum Conservation",
        syllabusCode: "9702.2.1",
        pageNumber: 42,
        content:
          "Newton's second law of motion states that the resultant force acting on a body is directly proportional to the rate of change of linear momentum, acting in the same direction: $$F = \\frac{dp}{dt} = \\frac{d(mv)}{dt}$$ When mass $m$ is constant, this reduces to the familiar formulation $F = ma$. In any closed system with zero external resultant forces, total linear momentum is strictly conserved: $$\\sum p_{\\text{initial}} = \\sum p_{\\text{final}}$$",
        keyFormulas: [
          "F = \\frac{\\Delta p}{\\Delta t}",
          "p = mv",
          "\\Delta p = F\\Delta t",
        ],
        verifiedCitationSnippet:
          "Newton's second law of motion states that the resultant force acting on a body is directly proportional to the rate of change of linear momentum.",
      },
      {
        id: "sec_waves_superposition",
        sectionNumber: "4.1",
        title: "Superposition of Waves & Double-Slit Interference",
        syllabusCode: "9702.4.1",
        pageNumber: 98,
        content:
          "The principle of superposition states that when two or more waves meet at a point in space, the resultant displacement is the algebraic sum of the individual displacements. In Young's double-slit experiment, monochromatic coherent light passing through two slits separated by distance $a$ produces an interference pattern on a screen at distance $D$ with fringe separation $x$: $$x = \\frac{\\lambda D}{a}$$ Increasing slit separation $a$ causes the fringes to become more closely spaced.",
        keyFormulas: [
          "x = \\frac{\\lambda D}{a}",
          "d\\sin\\theta = n\\lambda",
          "I \\propto A^2",
        ],
        verifiedCitationSnippet:
          "In Young's double-slit experiment, monochromatic coherent light produces fringe separation $x = \\frac{\\lambda D}{a}$.",
      },
      {
        id: "sec_waves_doppler",
        sectionNumber: "4.3",
        title: "The Doppler Effect for Sound and Light Waves",
        syllabusCode: "9702.4.3",
        pageNumber: 118,
        content:
          "When a wave source moves relative to an observer, the observed frequency $f_o$ changes because wave crests are compressed or dilated in the direction of motion. If a source emitting frequency $f_s$ moves towards a stationary observer with speed $v_s$ in a medium with wave speed $v$, the observed wavelength is compressed to $\\lambda' = \\frac{v - v_s}{f_s}$, resulting in an increased observed frequency: $$f_o = f_s\\left(\\frac{v}{v - v_s}\\right)$$ Conversely, for a receding source, the observed frequency decreases: $$f_o = f_s\\left(\\frac{v}{v + v_s}\\right)$$",
        keyFormulas: [
          "f_o = f_s\\left(\\frac{v}{v \\pm v_s}\\right)",
          "\\lambda' = \\frac{v \\mp v_s}{f_s}",
          "\\frac{\\Delta f}{f} \\approx \\frac{v}{c}",
        ],
        verifiedCitationSnippet:
          "When a wave source moves relative to an observer, the observed frequency $f_o$ changes because wave crests are compressed or dilated in the direction of motion.",
      },
    ],
  },
  {
    id: "doc_cambridge_physics_formula_sheet",
    title: "Cambridge International Physics Data & Formulae Sheet",
    examBoard: "Cambridge Assessment International Education",
    type: "formula_sheet",
    author: "Cambridge Examination Board",
    edition: "2026 Examination Series Reference",
    totalPages: 8,
    description:
      "Official reference formulas, physical constants, and conversion factors provided in Cambridge 9702 examinations.",
    sections: [
      {
        id: "sec_constants",
        sectionNumber: "F.1",
        title: "Physical Constants & Conversion Factors",
        syllabusCode: "9702.F.1",
        pageNumber: 2,
        content:
          "Standard physical constants verified for examination use: Speed of light in vacuum $c = 3.00 \\times 10^8\\text{ m/s}$, Elementary charge $e = 1.60 \\times 10^{-19}\\text{ C}$, Acceleration of free fall $g = 9.81\\text{ m/s}^2$, Planck constant $h = 6.63 \\times 10^{-34}\\text{ J}\\cdot\\text{s}$.",
        keyFormulas: [
          "c = 3.00 \\times 10^8\\text{ m/s}",
          "g = 9.81\\text{ m/s}^2",
          "e = 1.60 \\times 10^{-19}\\text{ C}",
          "h = 6.63 \\times 10^{-34}\\text{ J}\\cdot\\text{s}",
        ],
      },
      {
        id: "sec_optics_formulas",
        sectionNumber: "F.2",
        title: "Waves, Optics & Quantum Formulas",
        syllabusCode: "9702.F.2",
        pageNumber: 4,
        content:
          "Official examination wave formulas: Wave speed $v = f\\lambda$, Double slit fringe spacing $x = \\frac{\\lambda D}{a}$, Diffraction grating $d\\sin\\theta = n\\lambda$, Doppler effect $f_o = \\frac{f_s v}{v \\pm v_s}$.",
        keyFormulas: [
          "v = f\\lambda",
          "x = \\frac{\\lambda D}{a}",
          "d\\sin\\theta = n\\lambda",
          "E = hf = \\frac{hc}{\\lambda}",
        ],
      },
    ],
  },
  {
    id: "doc_ap_calc_bc_ced",
    title: "AP Calculus BC Course and Exam Description",
    examBoard: "College Board",
    type: "syllabus",
    author: "Advanced Placement Program",
    edition: "Effective Fall 2024",
    totalPages: 210,
    description:
      "Official curriculum framework delineating required skills, unit weightings, and learning objectives for AP Calculus BC.",
    sections: [
      {
        id: "sec_ap_series",
        sectionNumber: "10.1",
        title: "Taylor and Maclaurin Power Series Representations",
        syllabusCode: "AP-BC-10.1",
        pageNumber: 142,
        content:
          "The Taylor series of a smooth function $f(x)$ centered at $x = c$ is defined by: $$f(x) = \\sum_{n=0}^{\\infty} \\frac{f^{(n)}(c)}{n!}(x - c)^n$$ When centered at $c = 0$, the series is called a Maclaurin series. Common Maclaurin series include: $$e^x = \\sum_{n=0}^{\\infty} \\frac{x^n}{n!}, \\quad \\sin x = \\sum_{n=0}^{\\infty} \\frac{(-1)^n x^{2n+1}}{(2n+1)!}$$",
        keyFormulas: [
          "f(x) = \\sum_{n=0}^{\\infty}\\frac{f^{(n)}(c)}{n!}(x - c)^n",
          "e^x = 1 + x + \\frac{x^2}{2!} + \\dots",
          "\\sin x = x - \\frac{x^3}{3!} + \\frac{x^5}{5!} - \\dots",
        ],
      },
    ],
  },
];

export const resourceClient = {
  async getDocuments(): Promise<CurriculumDocument[]> {
    return SAMPLE_CURRICULUM_DOCUMENTS;
  },
  async getDocumentById(id: string): Promise<CurriculumDocument | undefined> {
    return SAMPLE_CURRICULUM_DOCUMENTS.find((d) => d.id === id);
  },
};
