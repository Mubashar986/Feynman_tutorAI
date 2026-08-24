import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { App } from "./App";
import { LaTeXRenderer } from "./components/common/LaTeXRenderer";
import { useAuthStore } from "./stores/authStore";
import { useCurriculumStore } from "./stores/curriculumStore";
import { useExamPlayerStore } from "./stores/examPlayerStore";
import { useSocraticTutorStore } from "./stores/socraticTutorStore";
import { useAnalyticsStore } from "./stores/analyticsStore";
import { useMisconceptionDAGStore } from "./stores/misconceptionDAGStore";
import { useExamSimulationStore } from "./stores/examSimulationStore";
import { useResourceManagerStore } from "./stores/resourceManagerStore";

describe("App & UI Primitives Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setActiveExam("exam_cambridge_physics_9702");
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useCurriculumStore.getState().setSearchQuery("");
    useExamPlayerStore.getState().resetSession();
    useSocraticTutorStore.getState().closeDrawer();
    useSocraticTutorStore.getState().clearHistory();
    useAnalyticsStore.getState().resetAnalytics();
    useMisconceptionDAGStore.getState().resetView();
    useExamSimulationStore.getState().resetSimulation();
    useResourceManagerStore.getState().resetView();
    localStorage.clear();
  });

  it("renders platform header and core branding", () => {
    render(<App />);
    expect(screen.getByText("Feynman Tutor AI")).toBeInTheDocument();
    expect(screen.getByText("Adaptive Exam Learning Platform")).toBeInTheDocument();
  });

  it("toggles dark mode class on document element", () => {
    render(<App />);
    const themeBtn = screen.getByLabelText("Toggle theme");
    expect(document.documentElement.classList.contains("dark")).toBe(false);

    fireEvent.click(themeBtn);
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    fireEvent.click(themeBtn);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});

describe("Curriculum Blueprint Catalog & Syllabus Tree Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setActiveExam("exam_cambridge_physics_9702");
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useCurriculumStore.getState().setSearchQuery("");
    useExamPlayerStore.getState().resetSession();
    useSocraticTutorStore.getState().closeDrawer();
    useAnalyticsStore.getState().resetAnalytics();
    useMisconceptionDAGStore.getState().resetView();
    useExamSimulationStore.getState().resetSimulation();
    useResourceManagerStore.getState().resetView();
    localStorage.clear();
  });

  it("renders the syllabus tree explorer by default", async () => {
    render(<App />);
    expect(screen.getByText(/Syllabus Taxonomy & Prerequisite Tree/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/1. Classical Mechanics & Kinematics/i)).toBeInTheDocument();
    });
  });

  it("switches to Exam Catalog tab and selects AP Calculus BC blueprint", async () => {
    render(<App />);

    const catalogTabs = screen.getAllByRole("button", { name: /Exam Catalog/i });
    fireEvent.click(catalogTabs[0]);

    expect(screen.getByText("Curriculum Blueprint Catalog")).toBeInTheDocument();
    expect(screen.getByText("AP Calculus BC")).toBeInTheDocument();
    expect(screen.getByText("Digital SAT Mathematics")).toBeInTheDocument();

    const selectBtns = screen.getAllByRole("button", { name: /Select & Explore Syllabus/i });
    fireEvent.click(selectBtns[0]);

    await waitFor(() => {
      expect(screen.getByText(/1. Differential Calculus & Applications/i)).toBeInTheDocument();
    });
  });

  it("filters syllabus topics dynamically via search input", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/1. Classical Mechanics & Kinematics/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search topics, formulas, or syllabus codes/i);
    fireEvent.change(searchInput, { target: { value: "Doppler" } });

    await waitFor(() => {
      expect(screen.getByText(/Doppler Effect in Sound & Light/i)).toBeInTheDocument();
    });
  });

  it("opens TopicDetailDrawer when clicking Inspect Objectives button", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Kinematics & Motion Graphs/i)).toBeInTheDocument();
    });

    const inspectBtns = screen.getAllByRole("button", { name: /Inspect/i });
    fireEvent.click(inspectBtns[0]);

    await waitFor(() => {
      expect(screen.getByText("Syllabus Learning Objectives (2)")).toBeInTheDocument();
      expect(screen.getByText("§ 9702.1.1")).toBeInTheDocument();
    });
  });
});

describe("Interactive Exam Taking Player Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().setAuth(
      {
        id: "student_alex",
        email: "alex@feynman.ai",
        fullName: "Alex Rivera",
        role: "student",
        targetExam: "Cambridge A-Level Physics",
      },
      "demo_jwt_token"
    );
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useExamPlayerStore.getState().resetSession();
    useSocraticTutorStore.getState().closeDrawer();
    useAnalyticsStore.getState().resetAnalytics();
    useMisconceptionDAGStore.getState().resetView();
    useExamSimulationStore.getState().resetSimulation();
    useResourceManagerStore.getState().resetView();
    localStorage.clear();
  });

  it("renders live exam player, countdown timer, and question palette", () => {
    render(<App />);

    const playerTabs = screen.getAllByRole("button", { name: /Exam Player/i });
    fireEvent.click(playerTabs[0]);

    expect(screen.getByText("Cambridge A-Level Physics Diagnostic Exam")).toBeInTheDocument();
    expect(screen.getByLabelText("Exam Time Remaining")).toBeInTheDocument();
    expect(screen.getByText("Question 1 of 5")).toBeInTheDocument();
    expect(screen.getByText("Question Palette")).toBeInTheDocument();
  });

  it("allows selecting an option, flagging for review, and jumping via palette", () => {
    render(<App />);

    const playerTabs = screen.getAllByRole("button", { name: /Exam Player/i });
    fireEvent.click(playerTabs[0]);

    const optionA = screen.getByLabelText("Option A");
    fireEvent.click(optionA);

    const flagBtn = screen.getByRole("button", { name: /Flag/i });
    fireEvent.click(flagBtn);

    expect(screen.getByRole("button", { name: /Flagged/i })).toBeInTheDocument();

    const q3Btn = screen.getByRole("button", { name: "Jump to Question 3" });
    fireEvent.click(q3Btn);

    expect(screen.getByText("Question 3 of 5")).toBeInTheDocument();
    expect(screen.getByText("Doppler Effect in Sound & Light")).toBeInTheDocument();
  });

  it("submits exam and renders diagnostic score report with derivations", async () => {
    render(<App />);

    const playerTabs = screen.getAllByRole("button", { name: /Exam Player/i });
    fireEvent.click(playerTabs[0]);

    fireEvent.click(screen.getByLabelText("Option A"));

    const finishBtn = screen.getByRole("button", { name: /Finish Test/i });
    fireEvent.click(finishBtn);

    expect(screen.getByText("Submit Exam For Scoring?")).toBeInTheDocument();

    const confirmBtn = screen.getByRole("button", { name: /Confirm & Grade Answers/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(/Completed diagnostic assessment/i)).toBeInTheDocument();
      expect(screen.getByText("Syllabus Topic Mastery Breakdown")).toBeInTheDocument();
      expect(screen.getByText(/Detailed Question Explanations/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Retake Diagnostic/i })).toBeInTheDocument();
    });
  });
});

describe("Student Analytics & Error Bank Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().setAuth(
      {
        id: "student_alex",
        email: "alex@feynman.ai",
        fullName: "Alex Rivera",
        role: "student",
        targetExam: "Cambridge A-Level Physics",
      },
      "demo_jwt_token"
    );
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useExamPlayerStore.getState().resetSession();
    useSocraticTutorStore.getState().closeDrawer();
    useAnalyticsStore.getState().resetAnalytics();
    useMisconceptionDAGStore.getState().resetView();
    useExamSimulationStore.getState().resetSimulation();
    useResourceManagerStore.getState().resetView();
    localStorage.clear();
  });

  it("renders the analytics dashboard, telemetry cards, and SVG radar chart", () => {
    render(<App />);

    const analyticsTabs = screen.getAllByRole("button", { name: /Analytics/i });
    fireEvent.click(analyticsTabs[0]);

    expect(screen.getByText(/88% Probability of Mastery/i)).toBeInTheDocument();
    expect(screen.getByText(/Solved Problems/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Streak/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Student Mastery Radar Chart")).toBeInTheDocument();
    expect(screen.getByText(/Bayesian Knowledge Tracing by Topic/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Kinematics & Motion Graphs/i).length).toBeGreaterThan(0);
  });

  it("filters error bank items by category and marks an error as resolved", () => {
    render(<App />);

    const analyticsTabs = screen.getAllByRole("button", { name: /Analytics/i });
    fireEvent.click(analyticsTabs[0]);

    expect(screen.getByText(/Diagnostic Error Bank & Misconception Log/i)).toBeInTheDocument();

    const formulaBtn = screen.getByRole("button", { name: /Formula Inversions/i });
    fireEvent.click(formulaBtn);

    expect(screen.getAllByText(/Superposition & Interference/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Fringe Width Geometric Inversion/i)).toBeInTheDocument();
    expect(screen.queryByText(/Approaching Source Frequency Dilation/i)).not.toBeInTheDocument();

    // Click card to expand details
    fireEvent.click(screen.getByText(/Fringe Width Geometric Inversion/i));

    const resolveBtn = screen.getByRole("button", { name: /Mark as Mastered/i });
    fireEvent.click(resolveBtn);

    expect(screen.getByRole("button", { name: /Resolved/i })).toBeInTheDocument();
  });
});

describe("Interactive Misconception DAG Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useExamPlayerStore.getState().resetSession();
    useSocraticTutorStore.getState().closeDrawer();
    useAnalyticsStore.getState().resetAnalytics();
    useMisconceptionDAGStore.getState().resetView();
    useExamSimulationStore.getState().resetSimulation();
    useResourceManagerStore.getState().resetView();
    localStorage.clear();
  });

  it("renders the interactive DAG canvas and node inspector", () => {
    render(<App />);

    const dagTabs = screen.getAllByRole("button", { name: /DAG/i });
    fireEvent.click(dagTabs[0]);

    expect(screen.getByText(/Prerequisite Knowledge & Misconception DAG/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Curriculum Misconception Directed Acyclic Graph")).toBeInTheDocument();

    // Default selected node inspector
    expect(screen.getAllByText(/Superposition & Interference/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Fringe Spacing Formula Inversion/i)).toBeInTheDocument();
  });

  it("selects a node on canvas and launches an adversarial challenge probe", async () => {
    render(<App />);

    const dagTabs = screen.getAllByRole("button", { name: /DAG/i });
    fireEvent.click(dagTabs[0]);

    // Launch Adversarial Challenge on selected Superposition node
    const advBtn = screen.getByRole("button", { name: /Launch Adversarial Challenge/i });
    fireEvent.click(advBtn);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Socratic AI Tutor" })).toBeInTheDocument();
      expect(screen.getAllByText(/Superposition & Interference/i).length).toBeGreaterThan(0);
    });
  });
});

describe("Full-Length Exam Readiness Simulation Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().setAuth(
      {
        id: "student_alex",
        email: "alex@feynman.ai",
        fullName: "Alex Rivera",
        role: "student",
        targetExam: "Cambridge A-Level Physics",
      },
      "demo_jwt_token"
    );
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useExamPlayerStore.getState().resetSession();
    useSocraticTutorStore.getState().closeDrawer();
    useAnalyticsStore.getState().resetAnalytics();
    useMisconceptionDAGStore.getState().resetView();
    useExamSimulationStore.getState().resetSimulation();
    useResourceManagerStore.getState().resetView();
    localStorage.clear();
  });

  it("renders simulation launcher, blueprint selector, and topic weights", () => {
    render(<App />);

    const simTabs = screen.getAllByRole("button", { name: /Simulation/i });
    fireEvent.click(simTabs[0]);

    expect(screen.getByText(/Full-Length Exam Simulation Engine/i)).toBeInTheDocument();
    expect(screen.getByText(/Configure Simulation Mode/i)).toBeInTheDocument();
    expect(screen.getByText(/Blueprint Topic Weighting Breakdown/i)).toBeInTheDocument();

    // Switch blueprint to AP Calculus BC
    const apBlueprintCard = screen.getByText(/AP Calculus BC Full Simulation Exam/i);
    fireEvent.click(apBlueprintCard);

    expect(screen.getByText("105 Minutes")).toBeInTheDocument();
    expect(screen.getByText("45 Questions")).toBeInTheDocument();
  });

  it("views calibrated diagnostic score report and print export", () => {
    render(<App />);

    const simTabs = screen.getAllByRole("button", { name: /Simulation/i });
    fireEvent.click(simTabs[0]);

    const sampleReportBtn = screen.getByRole("button", { name: /View Sample Diagnostic Report/i });
    fireEvent.click(sampleReportBtn);

    // Check report header
    expect(screen.getByText(/Calibrated Readiness Certificate/i)).toBeInTheDocument();
    expect(screen.getByText(/Predicted Exam Grade:/i)).toBeInTheDocument();
    expect(screen.getByText("87.5%")).toBeInTheDocument();

    // Check pacing telemetry
    expect(screen.getByText("68s")).toBeInTheDocument();
    expect(screen.getByText("Optimal")).toBeInTheDocument();

    // Check print button and back button
    expect(screen.getByRole("button", { name: /Export \/ Print Diagnostic Report/i })).toBeInTheDocument();
    const backBtn = screen.getByRole("button", { name: /Back to Blueprint Launcher/i });
    fireEvent.click(backBtn);

    expect(screen.getByText(/Full-Length Exam Simulation Engine/i)).toBeInTheDocument();
  });
});

describe("Curriculum Resource Hub & Grounded Document Viewer Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useExamPlayerStore.getState().resetSession();
    useSocraticTutorStore.getState().closeDrawer();
    useAnalyticsStore.getState().resetAnalytics();
    useMisconceptionDAGStore.getState().resetView();
    useExamSimulationStore.getState().resetSimulation();
    useResourceManagerStore.getState().resetView();
    localStorage.clear();
  });

  it("renders resource catalog, chapter index, and document reader", () => {
    render(<App />);

    const libraryTabs = screen.getAllByRole("button", { name: /Library/i });
    fireEvent.click(libraryTabs[0]);

    expect(screen.getByText(/Curriculum Resource Hub & Grounded Reader/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search textbook chapters, formulas, or syllabus codes/i)).toBeInTheDocument();
    expect(screen.getByText(/Table of Contents/i)).toBeInTheDocument();
    expect(screen.getByText(/Verified Curriculum Source Passage:/i)).toBeInTheDocument();
  });

  it("switches document and selects a section in the reader", () => {
    render(<App />);

    const libraryTabs = screen.getAllByRole("button", { name: /Library/i });
    fireEvent.click(libraryTabs[0]);

    // Select Formula Sheet
    const formulaSheetCard = screen.getByText(/Cambridge International Physics Data & Formulae Sheet/i);
    fireEvent.click(formulaSheetCard);

    expect(screen.getByText(/Waves, Optics & Quantum Formulas/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Ask Socratic Tutor/i })).toBeInTheDocument();
  });
});

describe("Socratic AI Tutor Drawer Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useExamPlayerStore.getState().resetSession();
    useSocraticTutorStore.getState().closeDrawer();
    useSocraticTutorStore.getState().clearHistory();
    useAnalyticsStore.getState().resetAnalytics();
    useMisconceptionDAGStore.getState().resetView();
    useExamSimulationStore.getState().resetSimulation();
    useResourceManagerStore.getState().resetView();
    localStorage.clear();
  });

  it("opens Socratic AI Tutor drawer when clicking floating action button", async () => {
    render(<App />);

    const floatBtn = screen.getByLabelText("Open Socratic AI Tutor");
    fireEvent.click(floatBtn);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Socratic AI Tutor" })).toBeInTheDocument();
      expect(screen.getByText(/Grounded interactive STEM guidance/i)).toBeInTheDocument();
    });
  });

  it("escalates progressive hints from Hint 1 to Hint 2", async () => {
    render(<App />);

    const floatBtn = screen.getByLabelText("Open Socratic AI Tutor");
    fireEvent.click(floatBtn);

    const hintBtn = screen.getByRole("button", { name: /Get Hint #1/i });
    fireEvent.click(hintBtn);

    await waitFor(() => {
      expect(screen.getByText(/Hint Level 1\/3:/i)).toBeInTheDocument();
      expect(screen.getByText(/governing physical principles/i)).toBeInTheDocument();
    });

    const hint2Btn = screen.getByRole("button", { name: /Get Hint #2/i });
    fireEvent.click(hint2Btn);

    await waitFor(() => {
      expect(screen.getByText(/Hint Level 2\/3:/i)).toBeInTheDocument();
    });
  });

  it("sends student prompt and receives Socratic guidance with citation", async () => {
    render(<App />);

    const floatBtn = screen.getByLabelText("Open Socratic AI Tutor");
    fireEvent.click(floatBtn);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Socratic AI Tutor" })).toBeInTheDocument();
    });

    const analogyBtn = screen.getByRole("button", { name: /Give me an analogy/i });
    fireEvent.click(analogyBtn);

    await waitFor(() => {
      expect(screen.getByText(/analogous physical example/i)).toBeInTheDocument();
    });
  });
});

describe("Authentication & Route Guard Flow Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useExamPlayerStore.getState().resetSession();
    useSocraticTutorStore.getState().closeDrawer();
    useAnalyticsStore.getState().resetAnalytics();
    useMisconceptionDAGStore.getState().resetView();
    useExamSimulationStore.getState().resetSimulation();
    useResourceManagerStore.getState().resetView();
    localStorage.clear();
  });

  it("shows unauthenticated state with RequireAuth prompt inside solver tab", () => {
    render(<App />);

    const solverTabs = screen.getAllByRole("button", { name: /Exam Player/i });
    fireEvent.click(solverTabs[0]);

    expect(screen.getByText("Authentication Required")).toBeInTheDocument();
  });

  it("logs in successfully via student demo quick-fill", async () => {
    render(<App />);

    const signInBtns = screen.getAllByRole("button", { name: /Sign In/i });
    fireEvent.click(signInBtns[0]);

    const demoBtn = screen.getByRole("button", { name: /Student Demo/i });
    fireEvent.click(demoBtn);

    const submitBtn = screen.getByRole("button", { name: /Sign In to Feynman/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Welcome back,/i)).toBeInTheDocument();
      expect(screen.getAllByText("Alex Rivera").length).toBeGreaterThan(0);
    });
  });
});

describe("LaTeXRenderer STEM Math Suite", () => {
  it("renders valid LaTeX formula into KaTeX HTML structure", () => {
    const { container } = render(<LaTeXRenderer formula="E = mc^2" />);
    expect(container.querySelector(".katex-rendered-wrapper")).toBeInTheDocument();
    expect(container.querySelector(".katex")).toBeInTheDocument();
  });

  it("gracefully falls back on malformed LaTeX without throwing", () => {
    const { container } = render(<LaTeXRenderer formula="\\frac{unclosed" />);
    expect(container.querySelector(".katex-rendered-wrapper")).toBeInTheDocument();
  });
});
