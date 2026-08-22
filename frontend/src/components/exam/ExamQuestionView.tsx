import * as React from "react";
import {
  ChevronLeft,
  ChevronRight,
  Flag,
  RotateCcw,
  CheckCircle2,
  HelpCircle,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import { useExamPlayerStore } from "@/stores/examPlayerStore";

export interface ExamQuestionViewProps {
  onOpenReviewModal?: () => void;
}

export const ExamQuestionView: React.FC<ExamQuestionViewProps> = ({
  onOpenReviewModal,
}) => {
  const {
    session,
    currentQuestionIndex,
    answers,
    flaggedQuestionIds,
    selectAnswer,
    clearAnswer,
    toggleFlag,
    nextQuestion,
    prevQuestion,
  } = useExamPlayerStore();

  const [showHint, setShowHint] = React.useState<boolean>(false);

  if (!session || !session.questions[currentQuestionIndex]) return null;

  const currentQ = session.questions[currentQuestionIndex];
  const selectedOptionId = answers[currentQ.id];
  const isFlagged = flaggedQuestionIds.includes(currentQ.id);
  const isLastQuestion = currentQuestionIndex === session.questions.length - 1;

  return (
    <Card className="flex flex-col justify-between border-border/80 shadow-md min-h-[460px]">
      <CardHeader className="space-y-3 border-b p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400 font-mono">
              Question {currentQuestionIndex + 1} of {session.questions.length}
            </span>
            <Badge variant="outline" className="text-xs">
              {currentQ.topicTitle}
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            {currentQ.irtDifficulty && (
              <Badge variant="masteryMedium" className="text-[10px]">
                Difficulty: {currentQ.irtDifficulty} IRT
              </Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => toggleFlag(currentQ.id)}
              className={`gap-1 text-xs transition-colors ${
                isFlagged
                  ? "border-amber-500 bg-amber-500/10 text-amber-600 dark:text-amber-400 font-bold"
                  : "text-muted-foreground"
              }`}
            >
              <Flag className={`h-3.5 w-3.5 ${isFlagged ? "fill-current" : ""}`} />
              <span>{isFlagged ? "Flagged [F]" : "Flag [F]"}</span>
            </Button>
          </div>
        </div>

        {/* Question Problem Stem with LaTeX Rendering */}
        <div className="pt-2 text-base leading-relaxed text-foreground font-medium">
          <LaTeXRenderer formula={currentQ.stemLatex} />
        </div>

        {/* Optional Socratic Hint Collapsible */}
        {currentQ.hintLatex && (
          <div className="pt-1">
            <button
              onClick={() => setShowHint(!showHint)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              <HelpCircle className="h-3.5 w-3.5" />
              {showHint ? "Hide Formula Hint" : "Need a Hint?"}
            </button>
            {showHint && (
              <div className="mt-2 rounded-md border border-indigo-500/30 bg-indigo-500/10 p-3 text-xs text-indigo-700 dark:text-indigo-300">
                <span className="font-semibold block mb-1">Pedagogical Hint:</span>
                <LaTeXRenderer formula={currentQ.hintLatex} />
              </div>
            )}
          </div>
        )}
      </CardHeader>

      {/* Options List */}
      <CardContent className="p-5 space-y-3">
        <div className="space-y-2.5">
          {currentQ.options.map((option) => {
            const isSelected = selectedOptionId === option.id;

            return (
              <button
                key={option.id}
                aria-label={option.label}
                onClick={() => selectAnswer(currentQ.id, option.id)}
                className={`group flex w-full items-center justify-between rounded-lg border p-4 text-left transition-all ${
                  isSelected
                    ? "border-indigo-600 bg-indigo-500/10 ring-2 ring-indigo-600 text-foreground"
                    : "border-border hover:border-border/80 hover:bg-muted/40 text-foreground"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md border text-xs font-bold transition-colors ${
                      isSelected
                        ? "bg-indigo-600 text-white border-indigo-600"
                        : "bg-muted text-muted-foreground group-hover:bg-muted/80"
                    }`}
                  >
                    {option.id}
                  </div>
                  <div className="text-sm">
                    <LaTeXRenderer formula={option.textLatex} />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="hidden sm:inline-block rounded border bg-muted/60 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                    {option.id}
                  </span>
                  {isSelected && (
                    <CheckCircle2 className="h-5 w-5 text-indigo-600 dark:text-indigo-400 shrink-0" />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </CardContent>

      {/* Navigation Footer */}
      <CardFooter className="flex items-center justify-between border-t p-4 bg-muted/10">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={prevQuestion}
            disabled={currentQuestionIndex === 0}
            className="text-xs gap-1"
          >
            <ChevronLeft className="h-4 w-4" /> Previous
          </Button>

          {selectedOptionId && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => clearAnswer(currentQ.id)}
              className="text-xs text-muted-foreground hover:text-foreground gap-1"
            >
              <RotateCcw className="h-3 w-3" /> Clear
            </Button>
          )}
        </div>

        <div>
          {isLastQuestion ? (
            <Button
              variant="mastery"
              size="sm"
              onClick={onOpenReviewModal}
              className="gap-1.5 text-xs font-bold"
            >
              <Sparkles className="h-3.5 w-3.5" /> Submit Exam
            </Button>
          ) : (
            <Button
              variant="tutor"
              size="sm"
              onClick={nextQuestion}
              className="gap-1 text-xs"
            >
              Next Question <ChevronRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
};
