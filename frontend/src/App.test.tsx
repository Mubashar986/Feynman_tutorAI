import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { App } from "./App";
import { LaTeXRenderer } from "./components/common/LaTeXRenderer";
import { useAuthStore } from "./stores/authStore";
import { useCurriculumStore } from "./stores/curriculumStore";

describe("App & UI Primitives Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setActiveExam("exam_cambridge_physics_9702");
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useCurriculumStore.getState().setSearchQuery("");
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

    // Click Exam Catalog tab in header
    const catalogTabs = screen.getAllByRole("button", { name: /Exam Catalog/i });
    fireEvent.click(catalogTabs[0]);

    // Verify Catalog Cards render
    expect(screen.getByText("Curriculum Blueprint Catalog")).toBeInTheDocument();
    expect(screen.getByText("AP Calculus BC")).toBeInTheDocument();
    expect(screen.getByText("Digital SAT Mathematics")).toBeInTheDocument();

    // Select AP Calculus BC (first 'Select & Explore' button in list)
    const selectBtns = screen.getAllByRole("button", { name: /Select & Explore Syllabus/i });
    fireEvent.click(selectBtns[0]);

    // Verify Syllabus tree updates with AP Calculus topics
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

    // Should display Doppler topic and hide irrelevant topics
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

    // Drawer should open and display formula objectives
    await waitFor(() => {
      expect(screen.getByText("Syllabus Learning Objectives (2)")).toBeInTheDocument();
      expect(screen.getByText("§ 9702.1.1")).toBeInTheDocument();
    });
  });
});

describe("Authentication & Route Guard Flow Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    useCurriculumStore.getState().setActiveExam("exam_cambridge_physics_9702");
    useCurriculumStore.getState().setSelectedTopic(null);
    useCurriculumStore.getState().setIsDrawerOpen(false);
    useCurriculumStore.getState().setSearchQuery("");
    localStorage.clear();
  });

  it("shows unauthenticated state with RequireAuth prompt inside solver tab", () => {
    render(<App />);

    // Navigate to Diagnostic Solver tab
    const solverTabs = screen.getAllByRole("button", { name: /Diagnostic Solver/i });
    fireEvent.click(solverTabs[0]);

    expect(screen.getByText("Authentication Required")).toBeInTheDocument();
  });

  it("logs in successfully via student demo quick-fill", async () => {
    render(<App />);

    // 1. Open Auth Dialog from Header
    const signInBtns = screen.getAllByRole("button", { name: /Sign In/i });
    fireEvent.click(signInBtns[0]);

    // 2. Click Student Demo quick fill
    const demoBtn = screen.getByRole("button", { name: /Student Demo/i });
    fireEvent.click(demoBtn);

    // 3. Submit Login
    const submitBtn = screen.getByRole("button", { name: /Sign In to Feynman/i });
    fireEvent.click(submitBtn);

    // 4. Verify authenticated session is active
    await waitFor(() => {
      expect(screen.getByText(/Welcome back,/i)).toBeInTheDocument();
      expect(screen.getAllByText("Alex Rivera").length).toBeGreaterThan(0);
    });
  });

  it("handles user logout and restores unauthenticated state", async () => {
    useAuthStore.getState().setAuth(
      {
        id: "test_user_01",
        email: "alex@feynman.ai",
        fullName: "Alex Rivera",
        role: "student",
        targetExam: "Cambridge A-Level Physics",
      },
      "dummy_jwt_token"
    );

    render(<App />);
    expect(screen.getAllByText("Alex Rivera").length).toBeGreaterThan(0);

    const userMenuBtn = screen.getByLabelText("User Profile Menu");
    fireEvent.click(userMenuBtn);

    const signOutBtn = screen.getByRole("button", { name: /Sign Out/i });
    fireEvent.click(signOutBtn);

    expect(screen.getAllByRole("button", { name: /Sign In/i }).length).toBeGreaterThan(0);
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
