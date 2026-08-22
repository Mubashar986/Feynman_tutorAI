import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { App } from "./App";
import { LaTeXRenderer } from "./components/common/LaTeXRenderer";

describe("App & UI Primitives Suite", () => {
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

  it("updates selected option state when user clicks an answer choice", () => {
    render(<App />);
    const optionA = screen.getByLabelText("Option A");
    expect(optionA).toBeInTheDocument();

    fireEvent.click(optionA);
    expect(screen.getByText(/Selected:/i)).toBeInTheDocument();
    expect(screen.getByText(/Option A/i)).toBeInTheDocument();
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
