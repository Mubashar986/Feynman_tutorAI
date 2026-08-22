import * as React from "react";
import {
  ShieldCheck,
  Sparkles,
  Clock,
  HelpCircle,
  Award,
  Layers,
  Flame,
  CheckCircle2,
  FileText,
  PlayCircle,
  Compass,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useExamSimulationStore } from "@/stores/examSimulationStore";
import { EXAM_BLUEPRINTS, SAMPLE_PHYSICS_SCORE_REPORT } from "@/api/simulation";
import type { ExamBlueprint, SimulationMode } from "@/types/simulation";

export interface ExamSimulationLauncherProps {
  onStartSimulation: (blueprint: ExamBlueprint, mode: SimulationMode) => void;
}

export const ExamSimulationLauncher: React.FC<ExamSimulationLauncherProps> = ({
  onStartSimulation,
}) => {
  const {
    activeBlueprint,
    setBlueprint,
    simulationMode,
    setSimulationMode,
    setScoreReport,
    simulationHistory,
  } = useExamSimulationStore();

  return (
    <div className="space-y-8 animate-in fade-in-50 duration-300">
      {/* 1. Master Simulation Banner */}
      <Card className="border-2 border-indigo-500/40 bg-gradient-to-br from-indigo-500/10 via-card to-card shadow-sm">
        <CardHeader className="p-6 pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Badge variant="masteryHigh" className="text-xs uppercase tracking-wider py-0.5 px-2.5">
                  Proctored Flight Simulator
                </Badge>
                <span className="text-xs text-muted-foreground font-mono">
                  Standardized Test Certification
                </span>
              </div>

              <CardTitle className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
                <ShieldCheck className="h-7 w-7 text-indigo-600 dark:text-indigo-400" />
                Full-Length Exam Simulation Engine
              </CardTitle>

              <CardDescription className="text-sm max-w-2xl">
                Experience realistic exam conditions with official topic distributions, drift-compensated chronometry, and psychometrically calibrated grade band predictions.
              </CardDescription>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setScoreReport(SAMPLE_PHYSICS_SCORE_REPORT)}
              className="self-start sm:self-auto text-xs gap-1.5 border-indigo-500/30 text-indigo-600 dark:text-indigo-400"
            >
              <FileText className="h-4 w-4" /> View Sample Diagnostic Report
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* 2. Blueprint Selection Grid */}
      <div className="space-y-3">
        <h3 className="text-base font-bold tracking-tight flex items-center gap-2 text-foreground">
          <Compass className="h-4 w-4 text-indigo-600" />
          Select Official Exam Blueprint
        </h3>

        <div className="grid gap-4 md:grid-cols-2">
          {EXAM_BLUEPRINTS.map((bp) => {
            const isSelected = activeBlueprint.id === bp.id;

            return (
              <div
                key={bp.id}
                onClick={() => setBlueprint(bp)}
                className={`cursor-pointer rounded-2xl border p-5 transition-all select-none ${
                  isSelected
                    ? "border-indigo-600 bg-indigo-500/5 ring-2 ring-indigo-600/30 shadow-md"
                    : "border-border/80 bg-card hover:border-border hover:shadow-xs"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                      {bp.examBoard}
                    </span>
                    <h4 className="text-base font-bold text-foreground">{bp.title}</h4>
                  </div>
                  {isSelected && (
                    <Badge variant="masteryHigh" className="text-[10px]">
                      Selected
                    </Badge>
                  )}
                </div>

                <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                  {bp.description}
                </p>

                <div className="mt-4 flex flex-wrap items-center gap-4 text-xs font-semibold text-muted-foreground border-t pt-3">
                  <span className="flex items-center gap-1.5 text-foreground">
                    <Clock className="h-3.5 w-3.5 text-indigo-600" /> {bp.durationMinutes} Minutes
                  </span>
                  <span className="flex items-center gap-1.5 text-foreground">
                    <HelpCircle className="h-3.5 w-3.5 text-indigo-600" /> {bp.totalQuestions} Questions
                  </span>
                  <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                    <Award className="h-3.5 w-3.5" /> Target: {bp.passingTargetScore}/{bp.totalQuestions}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Simulation Mode & Blueprint Topic Weighting */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* Left 6 Cols: Mode Configuration */}
        <Card className="lg:col-span-6 border-border/80 shadow-xs">
          <CardHeader className="p-5 pb-3 border-b">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-600" />
              Configure Simulation Mode
            </CardTitle>
            <CardDescription className="text-xs">
              Choose your test environment constraints and pedagogical scaffolding
            </CardDescription>
          </CardHeader>

          <CardContent className="p-5 space-y-4">
            {/* Mode Option 1: Proctored */}
            <div
              onClick={() => setSimulationMode("proctored")}
              className={`cursor-pointer rounded-xl border p-4 transition-all ${
                simulationMode === "proctored"
                  ? "border-indigo-600 bg-indigo-500/5 ring-1 ring-indigo-600"
                  : "border-border/80 bg-card hover:bg-muted/30"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-foreground flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-indigo-600" /> Strict Proctored Mock
                </span>
                <Badge variant={simulationMode === "proctored" ? "masteryHigh" : "outline"} className="text-[10px]">
                  Official Conditions
                </Badge>
              </div>
              <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
                Strict wall-clock countdown, zero Socratic hints, anti-cheat drift checks, and single-attempt scoring.
              </p>
            </div>

            {/* Mode Option 2: Guided */}
            <div
              onClick={() => setSimulationMode("guided")}
              className={`cursor-pointer rounded-xl border p-4 transition-all ${
                simulationMode === "guided"
                  ? "border-indigo-600 bg-indigo-500/5 ring-1 ring-indigo-600"
                  : "border-border/80 bg-card hover:bg-muted/30"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-foreground flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-500" /> Adaptive Guided Practice
                </span>
                <Badge variant={simulationMode === "guided" ? "masteryMedium" : "outline"} className="text-[10px]">
                  Scaffolded
                </Badge>
              </div>
              <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
                Pacing telemetry enabled with 3-tier progressive Socratic hints and instant misconception remediation.
              </p>
            </div>

            <div className="rounded-xl bg-muted/40 p-3.5 text-xs space-y-1 text-muted-foreground">
              <span className="font-semibold text-foreground block">Pacing Benchmark Target:</span>
              <p>
                Allocate approximately <strong className="text-foreground">{activeBlueprint.targetSecondsPerQuestion} seconds</strong> per question to maintain an optimal buffer for final review.
              </p>
            </div>
          </CardContent>

          <CardFooter className="border-t p-5">
            <Button
              variant="tutor"
              size="lg"
              onClick={() => onStartSimulation(activeBlueprint, simulationMode)}
              className="w-full gap-2 font-bold text-sm shadow-md"
            >
              <PlayCircle className="h-5 w-5" /> Launch {activeBlueprint.durationMinutes}-Minute Simulation
            </Button>
          </CardFooter>
        </Card>

        {/* Right 6 Cols: Blueprint Weighting Breakdown */}
        <Card className="lg:col-span-6 border-border/80 shadow-xs">
          <CardHeader className="p-5 pb-3 border-b">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Flame className="h-4 w-4 text-amber-500" />
              Blueprint Topic Weighting Breakdown
            </CardTitle>
            <CardDescription className="text-xs">
              Official syllabus domain distribution for {activeBlueprint.title}
            </CardDescription>
          </CardHeader>

          <CardContent className="p-5 space-y-4">
            {activeBlueprint.topicWeights.map((tw) => (
              <div key={tw.syllabusCode} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-foreground">{tw.topicTitle}</span>
                    <span className="ml-2 font-mono text-[11px] text-muted-foreground">
                      § {tw.syllabusCode}
                    </span>
                  </div>
                  <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                    {tw.weightPercentage}% ({tw.questionCount} Qs)
                  </span>
                </div>

                <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-indigo-600 rounded-full transition-all duration-500"
                    style={{ width: `${tw.weightPercentage}%` }}
                  />
                </div>
              </div>
            ))}

            {/* Historical Simulation Summary */}
            <div className="pt-3 border-t space-y-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block">
                Recent Simulation History:
              </span>
              {simulationHistory.slice(0, 2).map((h) => (
                <div
                  key={h.id}
                  onClick={() => setScoreReport(h)}
                  className="cursor-pointer flex items-center justify-between rounded-lg border bg-muted/20 p-2.5 text-xs hover:border-indigo-500/40 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    <div>
                      <span className="font-bold text-foreground block">{h.examTitle}</span>
                      <span className="text-[10px] text-muted-foreground">Date: {h.completionDate}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-extrabold text-indigo-600 dark:text-indigo-400 block">
                      {h.predictedGradeBand} ({h.percentage}%)
                    </span>
                    <span className="text-[10px] text-muted-foreground">{h.pacing.pacingStatus} Pace</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
