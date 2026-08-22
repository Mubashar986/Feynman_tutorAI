import * as React from "react";
import katex from "katex";
import { cn } from "@/lib/utils";

export interface LaTeXRendererProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** The LaTeX formula string to render */
  formula: string;
  /** If true, renders in display mode (centered block equation). If false, renders inline. */
  displayMode?: boolean;
  /** Whether to throw errors on invalid KaTeX syntax (defaults to false for graceful UI fallback) */
  throwOnError?: boolean;
}

/**
 * LaTeXRenderer — High-performance, safe KaTeX equation renderer.
 * Renders mathematical and physics formulas with zero Cumulative Layout Shift (CLS).
 */
export const LaTeXRenderer: React.FC<LaTeXRendererProps> = ({
  formula,
  displayMode = false,
  throwOnError = false,
  className,
  ...props
}) => {
  const containerRef = React.useRef<HTMLSpanElement>(null);

  const renderedHtml = React.useMemo(() => {
    try {
      return katex.renderToString(formula, {
        displayMode,
        throwOnError,
        trust: false, // Security: Never trust raw input for script/HTML injection
        strict: false,
      });
    } catch (err) {
      console.warn("KaTeX rendering error:", err);
      return `<span class="text-rose-500 font-mono text-xs">[LaTeX Error: ${escapeHtml(formula)}]</span>`;
    }
  }, [formula, displayMode, throwOnError]);

  return (
    <span
      ref={containerRef}
      className={cn(
        "katex-rendered-wrapper font-math",
        displayMode ? "my-3 block text-center overflow-x-auto py-1" : "inline-block align-baseline",
        className
      )}
      dangerouslySetInnerHTML={{ __html: renderedHtml }}
      {...props}
    />
  );
};

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
