import * as React from "react";
import { Flag, CheckCircle2, CircleDot } from "lucide-react";
import { useExamPlayerStore } from "@/stores/examPlayerStore";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export const QuestionPalette: React.FC = () => {
  const {
    session,
    currentQuestionIndex,
    answers,
    flaggedQuestionIds,
    goToQuestion,
  } = useExamPlayerStore();

  if (!session) return null;

  const totalQuestions = session.questions.length;
  const answeredCount = Object.keys(answers).length;
  const flaggedCount = flaggedQuestionIds.length;

  return (
    <Card className="border-border/80 shadow-sm">
      <CardHeader className="p-4 pb-3 border-b space-y-1.5">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold tracking-tight">Question Palette</CardTitle>
          <span className="text-[11px] font-medium text-muted-foreground">
            {answeredCount}/{totalQuestions} Answered
          </span>
        </div>

        {/* Legend status indicators */}
        <div className="flex flex-wrap gap-2 text-[10px] text-muted-foreground pt-1">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> Answered
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-amber-500" /> Flagged
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-slate-300 dark:bg-slate-700" /> Unanswered
          </span>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {/* Grid Matrix (1..N) */}
        <div className="grid grid-cols-5 gap-2">
          {session.questions.map((q, idx) => {
            const isAnswered = !!answers[q.id];
            const isFlagged = flaggedQuestionIds.includes(q.id);
            const isActive = currentQuestionIndex === idx;

            return (
              <button
                key={q.id}
                aria-label={`Jump to Question ${idx + 1}`}
                onClick={() => goToQuestion(idx)}
                className={`relative flex h-10 w-full items-center justify-center rounded-lg text-xs font-bold transition-all ${
                  isActive
                    ? "ring-2 ring-indigo-600 ring-offset-2 ring-offset-background font-extrabold"
                    : ""
                } ${
                  isAnswered
                    ? "bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/50 hover:bg-emerald-500/30"
                    : "bg-muted/40 text-muted-foreground border border-border hover:bg-muted/80"
                }`}
              >
                <span>{idx + 1}</span>

                {/* Flagged icon pip */}
                {isFlagged && (
                  <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-amber-500 text-white shadow-xs">
                    <Flag className="h-2 w-2 fill-current" />
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Status Breakdown Pill */}
        <div className="rounded-lg bg-muted/40 p-2.5 text-xs text-muted-foreground flex items-center justify-between">
          <span className="flex items-center gap-1.5 font-medium">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
            {answeredCount} Done
          </span>
          {flaggedCount > 0 && (
            <span className="flex items-center gap-1.5 font-medium text-amber-600 dark:text-amber-400">
              <Flag className="h-3.5 w-3.5" />
              {flaggedCount} Flagged
            </span>
          )}
          <span className="flex items-center gap-1.5 font-medium">
            <CircleDot className="h-3.5 w-3.5 text-slate-400" />
            {totalQuestions - answeredCount} Left
          </span>
        </div>
      </CardContent>
    </Card>
  );
};
