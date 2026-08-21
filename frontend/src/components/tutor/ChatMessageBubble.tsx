import * as React from "react";
import { Sparkles, User, BookOpen, ChevronDown, ChevronRight } from "lucide-react";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import type { SocraticMessage, SourceCitation } from "@/types/tutor";

export interface ChatMessageBubbleProps {
  message: SocraticMessage;
  isStreaming?: boolean;
}

/**
 * Parses mixed text and LaTeX equations ($...$ inline, $$...$$ display)
 * rendering math via KaTeX and prose as standard readable text.
 */
export const FormattedMathText: React.FC<{ text: string }> = ({ text }) => {
  if (!text) return null;

  // Split by display math $$...$$ first
  const displayParts = text.split(/(\$\$[\s\S]+?\$\$)/g);

  return (
    <div className="space-y-2 leading-relaxed">
      {displayParts.map((part, dIdx) => {
        if (part.startsWith("$$") && part.endsWith("$$")) {
          const formula = part.slice(2, -2).trim();
          return (
            <div key={dIdx} className="my-2 overflow-x-auto text-center">
              <LaTeXRenderer formula={formula} displayMode={true} />
            </div>
          );
        }

        // Split by inline math $...$
        const inlineParts = part.split(/(\$[^\$]+?\$)/g);
        return (
          <p key={dIdx} className="inline">
            {inlineParts.map((inlinePart, iIdx) => {
              if (inlinePart.startsWith("$") && inlinePart.endsWith("$") && inlinePart.length > 2) {
                const formula = inlinePart.slice(1, -1).trim();
                return (
                  <span key={iIdx} className="mx-0.5 inline-block align-baseline">
                    <LaTeXRenderer formula={formula} displayMode={false} />
                  </span>
                );
              }

              // Simple bold formatting **text**
              const boldParts = inlinePart.split(/(\*\*[^*]+?\*\*)/g);
              return (
                <React.Fragment key={iIdx}>
                  {boldParts.map((bPart, bIdx) => {
                    if (bPart.startsWith("**") && bPart.endsWith("**")) {
                      return (
                        <strong key={bIdx} className="font-bold text-foreground">
                          {bPart.slice(2, -2)}
                        </strong>
                      );
                    }
                    return <span key={bIdx}>{bPart}</span>;
                  })}
                </React.Fragment>
              );
            })}
          </p>
        );
      })}
    </div>
  );
};

export const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({
  message,
  isStreaming = false,
}) => {
  const [showThoughts, setShowThoughts] = React.useState<boolean>(false);
  const [activeCitation, setActiveCitation] = React.useState<SourceCitation | null>(null);

  if (message.role === "system") {
    return (
      <div className="flex justify-center my-2">
        <span className="rounded-full bg-muted px-3 py-1 text-[11px] font-medium text-muted-foreground border">
          {message.text}
        </span>
      </div>
    );
  }

  const isUser = message.role === "user";

  return (
    <div
      className={`flex gap-3 text-sm leading-relaxed ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar Icon */}
      <div
        className={`flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full shadow-xs ${
          isUser
            ? "bg-slate-700 text-white"
            : "bg-indigo-600 text-white shadow-indigo-500/20"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
      </div>

      {/* Message Content Bubble */}
      <div className={`max-w-[85%] space-y-2 ${isUser ? "text-right" : "text-left"}`}>
        {/* Tutor Reasoning Trace (Collapsible) */}
        {!isUser && message.thoughts && (
          <div className="rounded-md border border-indigo-500/20 bg-indigo-500/5 p-2 text-xs">
            <button
              onClick={() => setShowThoughts(!showThoughts)}
              className="flex items-center gap-1 font-semibold text-indigo-600 dark:text-indigo-400 text-[11px] hover:underline"
            >
              {showThoughts ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              AI Pedagogical Strategy
            </button>
            {showThoughts && (
              <p className="mt-1 text-muted-foreground italic text-[11px] leading-normal">
                {message.thoughts}
              </p>
            )}
          </div>
        )}

        <div
          className={`inline-block rounded-2xl px-4 py-3 shadow-xs ${
            isUser
              ? "bg-indigo-600 text-white rounded-tr-xs"
              : "bg-card border border-border/80 text-card-foreground rounded-tl-xs"
          }`}
        >
          {/* Main Message Text with Parsed Math & Prose */}
          <div className="space-y-1">
            <FormattedMathText text={message.text} />
            {isStreaming && (
              <span className="inline-block h-4 w-1.5 animate-pulse bg-indigo-600 dark:bg-indigo-400 ml-0.5 align-middle" />
            )}
          </div>
        </div>

        {/* Source Citation Pills */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-0.5">
            {message.citations.map((cite) => (
              <div key={cite.id} className="relative">
                <button
                  onClick={() =>
                    setActiveCitation(activeCitation?.id === cite.id ? null : cite)
                  }
                  className="inline-flex items-center gap-1 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 text-[10px] font-medium text-indigo-700 dark:text-indigo-300 hover:bg-indigo-500/20 transition-colors"
                >
                  <BookOpen className="h-2.5 w-2.5" />
                  <span>{cite.syllabusCode}</span>
                </button>

                {activeCitation?.id === cite.id && (
                  <div className="absolute left-0 bottom-full mb-2 w-72 rounded-lg border bg-popover p-3 shadow-xl text-popover-foreground text-xs z-50 animate-in fade-in-0 zoom-in-95">
                    <p className="font-semibold text-foreground">{cite.title}</p>
                    <p className="text-[10px] text-muted-foreground">
                      Page {cite.pageNumber || "N/A"} · Verified Curriculum Text
                    </p>
                    <p className="mt-1.5 text-muted-foreground italic border-t pt-1.5">
                      "{cite.snippet}"
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
