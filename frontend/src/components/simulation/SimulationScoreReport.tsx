import * as React from "react";
import {
  Trophy,
  Printer,
  RotateCcw,
  ArrowLeft,
  Clock,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Zap,
  BookOpen,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import type { CalibratedScoreReport } from "@/types/simulation";

export interface SimulationScoreReportProps {
  report: CalibratedScoreReport;
  onRetake: () => void;
  onBackToLauncher: () => void;
}

export const SimulationScoreReport: React.FC<SimulationScoreReportProps> = ({
  report,
  onRetake,
  onBackToLauncher,
}) => {
  const handlePrint = () => {
    if (typeof window !== "undefined" && window.print) {
      window.print();
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in-50 duration-300 print:m-0 print:p-0">
      {/* 1. Master Action Header (Hidden in Print) */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-4 print:hidden">
        <Button
          variant="outline"
          size="sm"
          onClick={onBackToLauncher}
          className="gap-1.5 text-xs"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Blueprint Launcher
        </Button>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrint}
            className="gap-1.5 text-xs border-indigo-500/30 text-indigo-600 dark:text-indigo-400 font-bold"
          >
            <Printer className="h-4 w-4" /> Export / Print Diagnostic Report
          </Button>

          <Button
            variant="tutor"
            size="sm"
            onClick={onRetake}
            className="gap-1.5 text-xs font-bold"
          >
            <RotateCcw className="h-4 w-4" /> Retake Simulation
          </Button>
        </div>
      </div>

      {/* 2. Official Flight Certification Banner */}
      <Card className="border-2 border-indigo-500/50 bg-gradient-to-br from-indigo-500/10 via-card to-card shadow-md print:border-black print:shadow-none">
        <CardHeader className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="masteryHigh" className="text-xs uppercase tracking-wider py-0.5 px-2.5">
                  Calibrated Readiness Certificate
                </Badge>
                <span className="font-mono text-xs text-muted-foreground">
                  Date: {report.completionDate}
                </span>
              </div>

              <CardTitle className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
                <Trophy className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                Predicted Exam Grade: <span className="text-indigo-600 dark:text-indigo-400">{report.predictedGradeBand}</span>
              </CardTitle>

              <CardDescription className="text-sm">
                Exam: <strong className="text-foreground">{report.examTitle}</strong> ({report.examBoard})
              </CardDescription>
            </div>

            <div className="flex items-center gap-4 rounded-xl border bg-card/80 p-4 shadow-xs self-start sm:self-auto print:border-black">
              <div className="text-right">
                <span className="block text-2xl font-extrabold text-indigo-600 dark:text-indigo-400 font-mono">
                  {report.percentage}%
                </span>
                <span className="text-[11px] text-muted-foreground">95% CI: [{report.confidenceInterval}]</span>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* 3. 4-Card Telemetry & Pacing Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4 space-y-1 shadow-xs border-border/80 print:border-black">
          <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Raw Score
          </span>
          <span className="block text-2xl font-extrabold text-foreground">
            {report.rawScore}/{report.totalQuestions}
          </span>
          <span className="text-[11px] text-muted-foreground">{report.percentage}% Accuracy</span>
        </Card>

        <Card className="p-4 space-y-1 shadow-xs border-border/80 print:border-black">
          <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-indigo-500" /> Average Pacing
          </span>
          <span className="block text-2xl font-extrabold text-indigo-600 dark:text-indigo-400 font-mono">
            {report.pacing.averageSecondsPerQuestion}s
          </span>
          <span className="text-[11px] text-muted-foreground">
            Target: {report.pacing.targetSecondsPerQuestion}s / question
          </span>
        </Card>

        <Card className="p-4 space-y-1 shadow-xs border-border/80 print:border-black">
          <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5 text-amber-500" /> Fastest Solve
          </span>
          <span className="block text-2xl font-extrabold text-foreground font-mono">
            {report.pacing.fastestQuestionSeconds}s
          </span>
          <span className="text-[11px] text-muted-foreground">Quickest Response</span>
        </Card>

        <Card className="p-4 space-y-1 shadow-xs border-border/80 print:border-black">
          <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-emerald-500" /> Pacing Status
          </span>
          <span className="block text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">
            {report.pacing.pacingStatus}
          </span>
          <span className="text-[11px] text-muted-foreground">Optimal Time Buffer</span>
        </Card>
      </div>

      {/* 4. Topic-Level Mastery Breakdown */}
      <Card className="border-border/80 shadow-xs print:border-black">
        <CardHeader className="p-5 pb-3 border-b">
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-indigo-600" />
            Syllabus Domain Mastery & Governing Formulations
          </CardTitle>
          <CardDescription className="text-xs">
            Detailed breakdown across official curriculum weighting modules
          </CardDescription>
        </CardHeader>

        <CardContent className="p-5 space-y-4">
          {report.topicBreakdowns.map((tb) => {
            const isMastered = tb.masteryTier === "Mastered";

            return (
              <div
                key={tb.syllabusCode}
                className="rounded-xl border border-border/80 bg-card p-4 space-y-2.5 print:border-black print:break-inside-avoid"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                      § {tb.syllabusCode}
                    </span>
                    <h4 className="text-sm font-bold text-foreground">{tb.topicTitle}</h4>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge
                      variant={isMastered ? "masteryHigh" : "masteryMedium"}
                      className="text-[10px]"
                    >
                      {isMastered ? (
                        <CheckCircle2 className="h-3 w-3 mr-1 inline" />
                      ) : (
                        <AlertCircle className="h-3 w-3 mr-1 inline" />
                      )}
                      {tb.masteryTier}
                    </Badge>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>
                      Accuracy: <strong className="text-foreground">{tb.accuracyPercentage}%</strong> ({tb.correctCount}/{tb.totalQuestions})
                    </span>
                  </div>

                  <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        tb.accuracyPercentage >= 80 ? "bg-emerald-500" : "bg-amber-500"
                      }`}
                      style={{ width: `${tb.accuracyPercentage}%` }}
                    />
                  </div>
                </div>

                {/* Governing Formulations in KaTeX */}
                <div className="pt-2 border-t text-xs text-muted-foreground flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase font-bold text-muted-foreground">
                    Governing Equations:
                  </span>
                  <LaTeXRenderer formula={tb.keyFormulaLatex} />
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
};
