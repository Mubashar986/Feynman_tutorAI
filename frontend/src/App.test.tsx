import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { App } from "./App";
import { LaTeXRenderer } from "./components/common/LaTeXRenderer";
import { useAuthStore } from "./stores/authStore";

describe("App & UI Primitives Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    localStorage.clear();
  });

  it("renders platform header and core branding", () => {
    render(<App />);
    expect(screen.getByText("Feynman Tutor AI")).toBeInTheDocument();
    expect(screen.getByText("Adaptive Exam Learning Platform")).toBeInTheDocument();
  });

  it("renders pedagogical mastery badge tokens", () => {
    render(<App />);
    expect(screen.getByText(/Mastered \(92%\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Developing \(68%\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Misconception \(34%\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Socratic Tutor Active/i)).toBeInTheDocument();
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

describe("Authentication & Route Guard Flow Suite", () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
    localStorage.clear();
  });

  it("shows unauthenticated state with RequireAuth prompt by default", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: /^Sign In$/i })).toBeInTheDocument();
    expect(screen.getByText("Authentication Required")).toBeInTheDocument();
  });

  it("logs in successfully via student demo quick-fill and unlocks protected solver", async () => {
    render(<App />);

    // 1. Open Auth Dialog from Header
    const signInBtn = screen.getByRole("button", { name: /^Sign In$/i });
    fireEvent.click(signInBtn);

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

    // 5. Verify protected problem solver is now accessible
    expect(screen.getByLabelText("Option A")).toBeInTheDocument();
  });

  it("handles user logout and restores protected route guard barrier", async () => {
    // Start with logged in state
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

    // Open User Profile Dropdown
    const userMenuBtn = screen.getByLabelText("User Profile Menu");
    fireEvent.click(userMenuBtn);

    // Click Sign Out
    const signOutBtn = screen.getByRole("button", { name: /Sign Out/i });
    fireEvent.click(signOutBtn);

    // Verify session cleared
    expect(screen.getByRole("button", { name: /^Sign In$/i })).toBeInTheDocument();
    expect(screen.getByText("Authentication Required")).toBeInTheDocument();
  });

  it("displays role-based access denial for student role on admin sections", () => {
    useAuthStore.getState().setAuth(
      {
        id: "student_user",
        email: "student@feynman.ai",
        fullName: "Student User",
        role: "student",
      },
      "token_student"
    );

    render(<App />);
    expect(
      screen.getByText(/Admin-only blueprint management tools are hidden/i)
    ).toBeInTheDocument();
  });

  it("allows registering a new student profile and hydrates session", async () => {
    render(<App />);

    // 1. Open Auth Dialog
    const signInBtn = screen.getByRole("button", { name: /^Sign In$/i });
    fireEvent.click(signInBtn);

    // 2. Switch to Register View
    const createAccountBtn = screen.getByRole("button", { name: /Create Account/i });
    fireEvent.click(createAccountBtn);

    // 3. Fill registration fields
    fireEvent.change(screen.getByLabelText(/Full Name/i), {
      target: { value: "Taylor Swift" },
    });
    fireEvent.change(screen.getByLabelText(/Email Address/i), {
      target: { value: "taylor@swift.edu" },
    });
    fireEvent.change(screen.getByLabelText(/Password \(min 6 characters\)/i), {
      target: { value: "securepassword123" },
    });

    // 4. Submit Registration
    const registerSubmitBtn = screen.getByRole("button", { name: /Start Adaptive Learning/i });
    fireEvent.click(registerSubmitBtn);

    // 5. Verify session is hydrated with new student
    await waitFor(() => {
      expect(screen.getAllByText("Taylor Swift").length).toBeGreaterThan(0);
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
