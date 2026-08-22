import * as React from "react";
import {
  Trophy,
  Flame,
  CheckCircle2,
  AlertTriangle,
  Compass,
  Layers,
  Sparkles,
  BookOpen,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAnalyticsStore } from "@/stores/analyticsStore";
import { MasteryRadarChart } from "./MasteryRadarChart";
import { TopicMasteryList } from "./TopicMasteryList";
import { ErrorBankList } from "./ErrorBankList";

export const AnalyticsDashboard: React.FC = () => {
  const { summary, topicMasteryRecords } = useAnalyticsStore();

  return (
    <div className="space-y-8 animate-in fade-in-50 duration-300">
      {/* 1. Master Exam Readiness Banner */}
      <Card className="border-2 border-indigo-500/40 bg-gradient-to-br from-indigo-500/10 via-card to-card shadow-sm">
        <CardHeader className="p-6 pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Badge variant="masteryHigh" className="text-xs uppercase tracking-wider py-0.5 px-2.5">
                  Calibrated Readiness Score
                </Badge>
                <span className="text-xs text-muted-foreground font-mono">
                  Cambridge Physics 9702
                </span>
              </div>

              <CardTitle className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
                <Trophy className="h-7 w-7 text-indigo-600 dark:text-indigo-400" />
                {summary.overallReadinessPercentage}% Probability of Mastery
              </CardTitle>

              <CardDescription className="text-sm">
                Predicted Grade Band: <strong className="text-foreground">{summary.estimatedGradeBand}</strong> based on adaptive Bayesian Knowledge Tracing.
              </CardDescription>
            </div>

            <div className="flex items-center gap-3 self-start sm:self-auto rounded-xl border bg-card/80 p-3 shadow-xs">
              <div className="text-right">
                <span className="block text-xl font-extrabold text-indigo-600 dark:text-indigo-400 font-mono">
                  {summary.overallAccuracy}%
                </span>
                <span className="text-[11px] text-muted-foreground">Historical Accuracy</span>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* 2. 4-Card KPI Telemetry Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4 space-y-1 shadow-xs border-border/80">
          <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Solved Problems
          </span>
          <span className="block text-2xl font-extrabold text-foreground">{summary.totalSolved}</span>
          <span className="text-[11px] text-muted-foreground">Across 5 Syllabus Topics</span>
        </Card>

        <Card className="p-4 space-y-1 shadow-xs border-border/80">
          <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
            <Flame className="h-3.5 w-3.5 text-amber-500" /> Active Streak
          </span>
          <span className="block text-2xl font-extrabold text-foreground">{summary.streakDays} Days</span>
          <span className="text-[11px] text-muted-foreground">Consistent Daily Practice</span>
        </Card>

        <Card className="p-4 space-y-1 shadow-xs border-border/80">
          <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-rose-500" /> Misconceptions
          </span>
          <span className="block text-2xl font-extrabold text-rose-600 dark:text-rose-400">
            {summary.activeMisconceptionsCount}
          </span>
          <span className="text-[11px] text-muted-foreground">Active in Error Bank</span>
        </Card>

        <Card className="p-4 space-y-1 shadow-xs border-border/80">
          <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-indigo-500" /> Errors Resolved
          </span>
          <span className="block text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">
            {summary.resolvedErrorsCount}
          </span>
          <span className="text-[11px] text-muted-foreground">Mastered after Remediation</span>
        </Card>
      </div>

      {/* 3. Multi-Axis Mastery: Split-Pane Radar & Topic List */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* Left: SVG Mastery Radar / Spider Chart */}
        <Card className="lg:col-span-6 border-border/80 shadow-xs flex flex-col justify-between">
          <CardHeader className="p-5 pb-2 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Compass className="h-4 w-4 text-indigo-600" />
                Multi-Axis Syllabus Mastery Radar
              </CardTitle>
              <Badge variant="outline" className="text-[10px]">
                5 Dimensions
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Normalized competency projection across syllabus domains
            </CardDescription>
          </CardHeader>

          <CardContent className="p-4 flex items-center justify-center min-h-[360px]">
            <MasteryRadarChart topics={topicMasteryRecords} size={340} />
          </CardContent>
        </Card>

        {/* Right: Topic Progress Breakdown */}
        <Card className="lg:col-span-6 border-border/80 shadow-xs">
          <CardHeader className="p-5 pb-3 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Layers className="h-4 w-4 text-indigo-600" />
                Bayesian Knowledge Tracing by Topic
              </CardTitle>
              <span className="text-xs text-muted-foreground font-mono">
                \(P(L_k)\) Probability
              </span>
            </div>
            <CardDescription className="text-xs">
              Topic-level accuracy and estimated latent mastery
            </CardDescription>
          </CardHeader>

          <CardContent className="p-4">
            <TopicMasteryList topics={topicMasteryRecords} />
          </CardContent>
        </Card>
      </div>

      {/* 4. Centralized Error Bank & Misconception Log */}
      <Card className="border-border/80 shadow-xs">
        <CardHeader className="p-6 pb-4 border-b">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-indigo-600" />
                Diagnostic Error Bank & Misconception Log
              </CardTitle>
              <CardDescription className="text-xs">
                Auditable queue of incorrect attempts with root-cause analysis and Socratic remediation
              </CardDescription>
            </div>

            <Badge variant="outline" className="self-start sm:self-auto text-xs">
              {summary.activeMisconceptionsCount} Active · {summary.resolvedErrorsCount} Resolved
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          <ErrorBankList />
        </CardContent>
      </Card>
    </div>
  );
};
