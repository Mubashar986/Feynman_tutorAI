import * as React from "react";
import {
  Trophy,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  XCircle,
  Clock,
  BookOpen,
  ChevronDown,
  ChevronRight,
  ArrowRight,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import { useExamPlayerStore } from "@/stores/examPlayerStore";

export interface ExamScoreReportProps {
  onReturnToSyllabus?: () => void;
  onOpenSocraticTutor?: () => void;
}

export const ExamScoreReport: React.FC<ExamScoreReportProps> = ({
  onReturnToSyllabus,
  onOpenSocraticTutor,
}) => {
  const { session, answers, scoreSummary, resetSession } = useExamPlayerStore();
  const [expandedQuestions, setExpandedQuestions] = React.useState<string[]>([]);

  if (!scoreSummary || !session) return null;

  const toggleQuestion = (qId: string) => {
    setExpandedQuestions((prev) =>
      prev.includes(qId) ? prev.filter((id) => id !== qId) : [...prev, qId]
    );
  };

  const minutesSpent = Math.floor(scoreSummary.timeSpentSeconds / 60);
  const secondsSpent = scoreSummary.timeSpentSeconds % 60;

  const isMastered = scoreSummary.scorePercentage >= 80;
  const isDeveloping =
    scoreSummary.scorePercentage >= 50 && scoreSummary.scorePercentage < 80;

  return (
    <div className="space-y-8 animate-in fade-in-50 duration-300">
      {/* Master Score Banner */}
      <Card
        className={`border-2 ${
          isMastered
            ? "border-emerald-500/50 bg-emerald-500/5"
            : isDeveloping
            ? "border-amber-500/50 bg-amber-500/5"
            : "border-rose-500/50 bg-rose-500/5"
        }`}
      >
        <CardHeader className="text-center space-y-3 pb-4">
          <div
            className={`mx-auto flex h-16 w-16 items-center justify-center rounded-2xl shadow-md ${
              isMastered
                ? "bg-emerald-600 text-white"
                : isDeveloping
                ? "bg-amber-500 text-white"
                : "bg-rose-500 text-white"
            }`}
          >
            <Trophy className="h-8 w-8" />
          </div>

          <div className="space-y-1">
            <Badge
              variant={
                isMastered
                  ? "masteryHigh"
                  : isDeveloping
                  ? "masteryMedium"
                  : "masteryLow"
              }
              className="text-xs font-bold uppercase tracking-wider py-1 px-3"
            >
              {isMastered
                ? "Mastery Demonstrated (>= 80%)"
                : isDeveloping
                ? "Developing Competence (50-79%)"
                : "Foundational Gap Detected (< 50%)"}
            </Badge>

            <CardTitle className="text-3xl font-extrabold tracking-tight sm:text-4xl text-foreground">
              {scoreSummary.scorePercentage}% Score
            </CardTitle>
            <CardDescription className="text-sm">
              {session.title} — Completed diagnostic assessment
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl border bg-card p-3 text-center shadow-xs">
              <span className="block text-2xl font-extrabold text-foreground">
                {scoreSummary.correctCount}/{scoreSummary.totalQuestions}
              </span>
              <span className="text-[11px] text-muted-foreground">Correct Answers</span>
            </div>
            <div className="rounded-xl border bg-card p-3 text-center shadow-xs">
              <span className="block text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">
                {scoreSummary.answeredCount}
              </span>
              <span className="text-[11px] text-muted-foreground">Attempted</span>
            </div>
            <div className="rounded-xl border bg-card p-3 text-center shadow-xs">
              <span className="block text-2xl font-extrabold text-indigo-600 dark:text-indigo-400 font-mono">
                {String(minutesSpent).padStart(2, "0")}:{String(secondsSpent).padStart(2, "0")}
              </span>
              <span className="text-[11px] text-muted-foreground flex items-center justify-center gap-1">
                <Clock className="h-3 w-3" /> Time Spent
              </span>
            </div>
            <div className="rounded-xl border bg-card p-3 text-center shadow-xs">
              <span className="block text-2xl font-extrabold text-amber-600 dark:text-amber-400">
                {scoreSummary.topicBreakdowns.length}
              </span>
              <span className="text-[11px] text-muted-foreground">Topics Graded</span>
            </div>
          </div>

          {/* Topic Mastery Breakdown */}
          <div className="space-y-3 rounded-xl border bg-card p-5">
            <h4 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-indigo-600" />
              Syllabus Topic Mastery Breakdown
            </h4>

            <div className="space-y-3 pt-1">
              {scoreSummary.topicBreakdowns.map((topic) => (
                <div key={topic.topicId} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-foreground truncate max-w-[220px] sm:max-w-none">
                      {topic.topicTitle}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-muted-foreground">
                        {topic.correctQuestions}/{topic.totalQuestions} ({topic.percentage}%)
                      </span>
                      <Badge
                        variant={
                          topic.masteryTier === "Mastered"
                            ? "masteryHigh"
                            : topic.masteryTier === "Developing"
                            ? "masteryMedium"
                            : "masteryLow"
                        }
                        className="text-[10px] py-0 px-2"
                      >
                        {topic.masteryTier}
                      </Badge>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        topic.percentage >= 80
                          ? "bg-emerald-500"
                          : topic.percentage >= 50
                          ? "bg-amber-500"
                          : "bg-rose-500"
                      }`}
                      style={{ width: `${topic.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Question by Question Review Accordion */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold tracking-tight text-foreground">
              Detailed Question Explanations & Derivations
            </h4>

            <div className="space-y-3">
              {session.questions.map((q, idx) => {
                const studentAns = answers[q.id];
                const isCorrect = studentAns === q.correctOptionId;
                const isExpanded =
                  expandedQuestions.includes(q.id) || !isCorrect;

                return (
                  <div
                    key={q.id}
                    className={`rounded-lg border transition-all ${
                      isCorrect
                        ? "border-emerald-500/30 bg-emerald-500/5"
                        : "border-rose-500/30 bg-rose-500/5"
                    }`}
                  >
                    <div
                      className="flex cursor-pointer select-none items-center justify-between p-4"
                      onClick={() => toggleQuestion(q.id)}
                    >
                      <div className="flex items-center gap-3">
                        {isCorrect ? (
                          <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                        ) : (
                          <XCircle className="h-5 w-5 text-rose-600 dark:text-rose-400 shrink-0" />
                        )}
                        <div>
                          <span className="font-mono text-xs font-bold text-foreground">
                            Question {idx + 1}: {q.topicTitle}
                          </span>
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            Your answer: <strong>{studentAns || "None"}</strong> · Correct: <strong>{q.correctOptionId}</strong>
                          </p>
                        </div>
                      </div>

                      <div className="text-muted-foreground">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="border-t p-4 space-y-3 bg-card/60 rounded-b-lg text-sm">
                        <div>
                          <span className="text-xs font-semibold text-muted-foreground uppercase block mb-1">
                            Problem Stem:
                          </span>
                          <LaTeXRenderer formula={q.stemLatex} />
                        </div>

                        <div className="rounded-md border border-indigo-500/30 bg-indigo-500/10 p-3.5 space-y-1.5 text-xs text-indigo-900 dark:text-indigo-200">
                          <span className="font-bold text-indigo-700 dark:text-indigo-300 block">
                            Step-by-Step Derivation & Explanation:
                          </span>
                          <LaTeXRenderer formula={q.explanationLatex} />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col sm:flex-row gap-3 pt-2">
          <Button
            variant="mastery"
            className="w-full sm:flex-1 gap-2"
            onClick={resetSession}
          >
            <RotateCcw className="h-4 w-4" /> Retake Diagnostic
          </Button>

          {onOpenSocraticTutor && (
            <Button
              variant="tutor"
              className="w-full sm:flex-1 gap-2"
              onClick={onOpenSocraticTutor}
            >
              <Sparkles className="h-4 w-4" /> Review with Socratic AI
            </Button>
          )}

          {onReturnToSyllabus && (
            <Button
              variant="outline"
              className="w-full sm:w-auto gap-1"
              onClick={onReturnToSyllabus}
            >
              Back to Syllabus <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
};
