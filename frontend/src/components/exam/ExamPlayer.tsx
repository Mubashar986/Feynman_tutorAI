import * as React from "react";
import {
  Sparkles,
  AlertCircle,
  ChevronRight,
  Shield,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { useExamPlayerStore } from "@/stores/examPlayerStore";
import { ExamTimer } from "./ExamTimer";
import { QuestionPalette } from "./QuestionPalette";
import { ExamQuestionView } from "./ExamQuestionView";
import { ExamScoreReport } from "./ExamScoreReport";

export interface ExamPlayerProps {
  onReturnToSyllabus?: () => void;
  onOpenSocraticTutor?: () => void;
}

export const ExamPlayer: React.FC<ExamPlayerProps> = ({
  onReturnToSyllabus,
  onOpenSocraticTutor,
}) => {
  const {
    session,
    currentQuestionIndex,
    answers,
    flaggedQuestionIds,
    isSubmitted,
    isReviewModalOpen,
    setIsReviewModalOpen,
    selectAnswer,
    toggleFlag,
    nextQuestion,
    prevQuestion,
    submitExam,
  } = useExamPlayerStore();

  // Keyboard navigation shortcuts listener
  React.useEffect(() => {
    if (isSubmitted || !session) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore keystrokes inside input or textarea elements
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        return;
      }

      const key = e.key.toUpperCase();
      const currentQ = session.questions[currentQuestionIndex];
      if (!currentQ) return;

      // Option Selection (A, B, C, D or 1, 2, 3, 4)
      if (["A", "B", "C", "D"].includes(key)) {
        e.preventDefault();
        selectAnswer(currentQ.id, key);
      } else if (["1", "2", "3", "4"].includes(key)) {
        e.preventDefault();
        const map: Record<string, string> = { "1": "A", "2": "B", "3": "C", "4": "D" };
        selectAnswer(currentQ.id, map[key]);
      } else if (e.key === "ArrowRight" || e.key.toLowerCase() === "k") {
        e.preventDefault();
        nextQuestion();
      } else if (e.key === "ArrowLeft" || e.key.toLowerCase() === "j") {
        e.preventDefault();
        prevQuestion();
      } else if (e.key.toLowerCase() === "f") {
        e.preventDefault();
        toggleFlag(currentQ.id);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    isSubmitted,
    session,
    currentQuestionIndex,
    selectAnswer,
    toggleFlag,
    nextQuestion,
    prevQuestion,
  ]);

  if (!session) return null;

  // Render Diagnostic Score Report if exam is submitted
  if (isSubmitted) {
    return (
      <ExamScoreReport
        onReturnToSyllabus={onReturnToSyllabus}
        onOpenSocraticTutor={onOpenSocraticTutor}
      />
    );
  }

  const totalQuestions = session.questions.length;
  const answeredCount = Object.keys(answers).length;
  const unansweredCount = totalQuestions - answeredCount;

  return (
    <div className="space-y-6">
      {/* Top Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border bg-card p-4 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold tracking-tight text-foreground">
              {session.title}
            </h2>
            <Badge variant="outline" className="font-mono text-[10px]">
              {session.code}
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Shield className="h-3 w-3 text-indigo-500" /> Proctored Test Mode
            </span>
            <span>·</span>
            <span>Shortcuts: <strong>[A-D]</strong> select, <strong>[F]</strong> flag, <strong>[←/→]</strong> nav</span>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-auto">
          <ExamTimer />
          <Button
            variant="mastery"
            size="sm"
            onClick={() => setIsReviewModalOpen(true)}
            className="gap-1.5 text-xs font-bold"
          >
            <Sparkles className="h-3.5 w-3.5" /> Finish Test
          </Button>
        </div>
      </div>

      {/* Split-Pane Stage: Left Question, Right Palette */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        <div className="lg:col-span-8">
          <ExamQuestionView
            onOpenReviewModal={() => setIsReviewModalOpen(true)}
          />
        </div>

        <div className="lg:col-span-4 space-y-4">
          <QuestionPalette />
        </div>
      </div>

      {/* Submission Confirmation Modal */}
      <Dialog open={isReviewModalOpen} onOpenChange={setIsReviewModalOpen}>
        <DialogContent className="sm:max-w-md p-0 overflow-hidden border-0 bg-transparent shadow-none">
          <Card className="w-full shadow-2xl border-border">
            <CardHeader className="space-y-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xl font-bold">Submit Exam For Scoring?</CardTitle>
                <Layers className="h-5 w-5 text-indigo-500" />
              </div>
              <CardDescription>
                Review your answering progress before finalizing your submission.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-2 rounded-lg bg-muted/40 p-3 text-center text-xs">
                <div>
                  <span className="block text-lg font-bold text-foreground">{totalQuestions}</span>
                  <span className="text-muted-foreground">Total</span>
                </div>
                <div>
                  <span className="block text-lg font-bold text-emerald-600 dark:text-emerald-400">
                    {answeredCount}
                  </span>
                  <span className="text-muted-foreground">Answered</span>
                </div>
                <div>
                  <span className={`block text-lg font-bold ${unansweredCount > 0 ? "text-rose-500" : "text-muted-foreground"}`}>
                    {unansweredCount}
                  </span>
                  <span className="text-muted-foreground">Unanswered</span>
                </div>
              </div>

              {unansweredCount > 0 && (
                <div
                  role="alert"
                  className="flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-300 font-medium"
                >
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>
                    You have <strong>{unansweredCount} unanswered</strong> questions. Unanswered questions will receive zero marks.
                  </span>
                </div>
              )}

              {flaggedQuestionIds.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  Note: You currently have <strong>{flaggedQuestionIds.length} flagged</strong> question(s).
                </p>
              )}
            </CardContent>

            <CardFooter className="flex justify-end gap-2 border-t p-4 bg-muted/10">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsReviewModalOpen(false)}
              >
                Return to Exam
              </Button>
              <Button
                variant="mastery"
                size="sm"
                onClick={submitExam}
                className="gap-1.5 font-bold"
              >
                Confirm & Grade Answers <ChevronRight className="h-4 w-4" />
              </Button>
            </CardFooter>
          </Card>
        </DialogContent>
      </Dialog>
    </div>
  );
};
