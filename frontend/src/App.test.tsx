import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { App } from "./App";
import { LaTeXRenderer } from "./components/common/LaTeXRenderer";
import { useAuthStore } from "./stores/authStore";
import { useCurriculumStore } from "./stores/curriculumStore";
import { useExamPlayerStore } from "./stores/examPlayerStore";

describe("App & UI Primitives Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setActiveExam("exam_cambridge_physics_9702");
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useCurriculumStore.getState().setSearchQuery("");
    useExamPlayerStore.getState().resetSession();
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
    // Authenticate student session
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
    localStorage.clear();
  });

  it("renders live exam player, countdown timer, and question palette", () => {
    render(<App />);

    // Switch to Exam Player tab
    const playerTabs = screen.getAllByRole("button", { name: /Interactive Exam Player/i });
    fireEvent.click(playerTabs[0]);

    // Verify Exam Header & Timer
    expect(screen.getByText("Cambridge A-Level Physics Diagnostic Exam")).toBeInTheDocument();
    expect(screen.getByLabelText("Exam Time Remaining")).toBeInTheDocument();
    expect(screen.getByText("Question 1 of 5")).toBeInTheDocument();
    expect(screen.getByText("Question Palette")).toBeInTheDocument();
  });

  it("allows selecting an option, flagging for review, and jumping via palette", () => {
    render(<App />);

    const playerTabs = screen.getAllByRole("button", { name: /Interactive Exam Player/i });
    fireEvent.click(playerTabs[0]);

    // Select Option A on Question 1
    const optionA = screen.getByLabelText("Option A");
    fireEvent.click(optionA);

    // Flag Question 1
    const flagBtn = screen.getByRole("button", { name: /Flag/i });
    fireEvent.click(flagBtn);

    // Question 1 should be flagged
    expect(screen.getByRole("button", { name: /Flagged/i })).toBeInTheDocument();

    // Jump to Question 3 via Question Palette
    const q3Btn = screen.getByRole("button", { name: "Jump to Question 3" });
    fireEvent.click(q3Btn);

    expect(screen.getByText("Question 3 of 5")).toBeInTheDocument();
    expect(screen.getByText("Doppler Effect in Sound & Light")).toBeInTheDocument();
  });

  it("submits exam and renders diagnostic score report with derivations", async () => {
    render(<App />);

    const playerTabs = screen.getAllByRole("button", { name: /Interactive Exam Player/i });
    fireEvent.click(playerTabs[0]);

    // Answer Question 1 correctly
    fireEvent.click(screen.getByLabelText("Option A"));

    // Click Finish Test
    const finishBtn = screen.getByRole("button", { name: /Finish Test/i });
    fireEvent.click(finishBtn);

    // Review Modal opens
    expect(screen.getByText("Submit Exam For Scoring?")).toBeInTheDocument();

    // Confirm Submission
    const confirmBtn = screen.getByRole("button", { name: /Confirm & Grade Answers/i });
    fireEvent.click(confirmBtn);

    // Diagnostic Score Report renders
    await waitFor(() => {
      expect(screen.getByText(/Completed diagnostic assessment/i)).toBeInTheDocument();
      expect(screen.getByText("Syllabus Topic Mastery Breakdown")).toBeInTheDocument();
      expect(screen.getByText(/Detailed Question Explanations/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Retake Diagnostic/i })).toBeInTheDocument();
    });
  });
});

describe("Authentication & Route Guard Flow Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useExamPlayerStore.getState().resetSession();
    localStorage.clear();
  });

  it("shows unauthenticated state with RequireAuth prompt inside solver tab", () => {
    render(<App />);

    const solverTabs = screen.getAllByRole("button", { name: /Interactive Exam Player/i });
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
