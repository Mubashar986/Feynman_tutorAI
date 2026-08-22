import * as React from "react";
import {
  Network,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Sparkles,
  ShieldAlert,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useMisconceptionDAGStore } from "@/stores/misconceptionDAGStore";
import { MisconceptionDAGCanvas } from "./MisconceptionDAGCanvas";
import { DAGNodeInspector } from "./DAGNodeInspector";

export const DAGVisualizer: React.FC = () => {
  const { filterMode, setFilterMode } = useMisconceptionDAGStore();

  const FILTER_OPTIONS: {
    id: "all" | "misconceptions" | "critical_path";
    label: string;
    icon: React.ReactNode;
  }[] = [
    { id: "all", label: "All Prerequisite Nodes", icon: <Network className="h-3.5 w-3.5" /> },
    {
      id: "misconceptions",
      label: "Active Misconceptions",
      icon: <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />,
    },
    {
      id: "critical_path",
      label: "Critical Bottlenecks",
      icon: <ShieldAlert className="h-3.5 w-3.5 text-amber-500" />,
    },
  ];

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-300">
      {/* 1. Header Card & Filter Toolbar */}
      <Card className="border-border/80 shadow-xs">
        <CardHeader className="p-5 pb-4 border-b space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge variant="masteryHigh" className="text-[10px] uppercase font-bold">
                  Curriculum Topology Engine
                </Badge>
                <span className="font-mono text-xs text-muted-foreground">
                  Cambridge Physics 9702
                </span>
              </div>

              <CardTitle className="text-xl sm:text-2xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
                <Network className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                Prerequisite Knowledge & Misconception DAG
              </CardTitle>

              <CardDescription className="text-xs sm:text-sm">
                Explore concept dependencies, diagnose mental model bottlenecks, and launch adversarial challenge probes.
              </CardDescription>
            </div>

            {/* Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5 self-start sm:self-auto rounded-xl border bg-muted/40 p-1">
              {FILTER_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setFilterMode(opt.id)}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                    filterMode === opt.id
                      ? "bg-card text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {opt.icon}
                  <span>{opt.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Status Legend Pills */}
          <div className="flex flex-wrap items-center gap-3 pt-2 text-[11px] text-muted-foreground border-t">
            <span className="font-semibold text-foreground">Legend:</span>
            <span className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-emerald-500" /> Mastered (&ge; 80%)
            </span>
            <span className="flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-amber-500" /> Developing (50-79%)
            </span>
            <span className="flex items-center gap-1">
              <AlertTriangle className="h-3 w-3 text-rose-500" /> Active Misconception (&lt; 50%)
            </span>
            <span className="flex items-center gap-1">
              <Lock className="h-3 w-3 text-slate-400" /> Locked (Prerequisite Blocked)
            </span>
          </div>
        </CardHeader>
      </Card>

      {/* 2. Main Stage: Split-Pane Canvas + Node Inspector */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* Left 8 Cols: Interactive SVG DAG Canvas */}
        <div className="lg:col-span-8">
          <MisconceptionDAGCanvas />
        </div>

        {/* Right 4 Cols: Selected Node Inspector & Action Triggers */}
        <div className="lg:col-span-4 space-y-4">
          <DAGNodeInspector />
        </div>
      </div>
    </div>
  );
};
