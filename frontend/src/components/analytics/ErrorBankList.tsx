import * as React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  ChevronDown,
  ChevronRight,
  Filter,
  BrainCircuit,
  Calculator,
  Binary,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import { useAnalyticsStore } from "@/stores/analyticsStore";
import { useSocraticTutorStore } from "@/stores/socraticTutorStore";

export const ErrorBankList: React.FC = () => {
  const {
    errorBankItems,
    selectedCategoryFilter,
    setCategoryFilter,
    resolveErrorItem,
  } = useAnalyticsStore();

  const { openDrawer: openSocraticDrawer } = useSocraticTutorStore();
  const [expandedErrorIds, setExpandedErrorIds] = React.useState<string[]>([
    "err_doppler_01",
  ]);

  const toggleExpand = (id: string) => {
    setExpandedErrorIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const filteredItems = errorBankItems.filter((item) => {
    if (selectedCategoryFilter === "all") return true;
    return item.category === selectedCategoryFilter;
  });

  const CATEGORIES: { id: string; label: string; icon: React.ReactNode }[] = [
    { id: "all", label: "All Errors", icon: <Filter className="h-3 w-3" /> },
    {
      id: "conceptual",
      label: "Conceptual Flaws",
      icon: <BrainCircuit className="h-3 w-3" />,
    },
    {
      id: "formula",
      label: "Formula Inversions",
      icon: <Binary className="h-3 w-3" />,
    },
    {
      id: "calculation",
      label: "Calculation Slips",
      icon: <Calculator className="h-3 w-3" />,
    },
  ];

  return (
    <div className="space-y-4">
      {/* Category Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-2 border-b pb-3">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setCategoryFilter(cat.id)}
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-all ${
              selectedCategoryFilter === cat.id
                ? "bg-indigo-600 text-white shadow-xs"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            {cat.icon}
            <span>{cat.label}</span>
          </button>
        ))}
      </div>

      {/* Filtered Error Cards List */}
      {filteredItems.length === 0 ? (
        <div className="rounded-xl border border-dashed p-8 text-center text-muted-foreground space-y-2">
          <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500" />
          <p className="font-semibold text-foreground">Zero Unresolved Errors in this Category</p>
          <p className="text-xs">Great job! All logged misconceptions here have been mastered.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredItems.map((item) => {
            const isExpanded = expandedErrorIds.includes(item.id);

            return (
              <div
                key={item.id}
                className={`rounded-xl border transition-all ${
                  item.isResolved
                    ? "border-border/60 bg-muted/20 opacity-75"
                    : "border-rose-500/30 bg-card shadow-xs hover:border-rose-500/50"
                }`}
              >
                {/* Header Row */}
                <div
                  className="flex cursor-pointer select-none items-center justify-between p-4"
                  onClick={() => toggleExpand(item.id)}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                        item.isResolved
                          ? "bg-emerald-500/10 text-emerald-600"
                          : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                      }`}
                    >
                      {item.isResolved ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : (
                        <AlertTriangle className="h-4 w-4" />
                      )}
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-muted-foreground">
                          § {item.syllabusCode}
                        </span>
                        <h4 className="text-sm font-bold text-foreground">
                          {item.topicTitle}
                        </h4>
                      </div>
                      <p className="text-xs text-rose-600 dark:text-rose-400 font-medium">
                        Misconception: {item.misconceptionTag}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        item.category === "conceptual"
                          ? "destructive"
                          : item.category === "formula"
                          ? "masteryMedium"
                          : "secondary"
                      }
                      className="text-[10px] uppercase font-bold"
                    >
                      {item.category}
                    </Badge>
                    <div className="text-muted-foreground">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Content Area */}
                {isExpanded && (
                  <div className="border-t p-4 space-y-4 bg-muted/10 rounded-b-xl text-xs sm:text-sm">
                    {/* Problem Stem */}
                    <div className="space-y-1">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                        Original Problem:
                      </span>
                      <div className="rounded-lg border bg-card p-3 font-medium text-foreground">
                        <LaTeXRenderer formula={item.problemStemLatex} />
                      </div>
                    </div>

                    {/* Answer Comparison */}
                    <div className="grid sm:grid-cols-2 gap-3">
                      <div className="rounded-lg border border-rose-500/30 bg-rose-500/5 p-3 space-y-1">
                        <span className="font-bold text-rose-700 dark:text-rose-400 block text-[11px] uppercase">
                          What You Answered:
                        </span>
                        <p className="text-xs text-foreground font-medium">
                          {item.studentAnswer}
                        </p>
                      </div>

                      <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3 space-y-1">
                        <span className="font-bold text-emerald-700 dark:text-emerald-400 block text-[11px] uppercase">
                          Correct Derivation:
                        </span>
                        <p className="text-xs text-foreground font-medium">
                          {item.correctAnswer}
                        </p>
                      </div>
                    </div>

                    {/* Root Misconception Diagnosis */}
                    <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 p-3.5 space-y-1.5">
                      <span className="font-bold text-indigo-700 dark:text-indigo-300 block text-xs flex items-center gap-1.5">
                        <Sparkles className="h-3.5 w-3.5" />
                        Root Cause Misconception Analysis:
                      </span>
                      <p className="text-xs text-indigo-950 dark:text-indigo-200 leading-relaxed">
                        {item.misconceptionDetail}
                      </p>
                    </div>

                    {/* Action Triggers */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={item.isResolved}
                        onClick={() => resolveErrorItem(item.id)}
                        className="text-xs gap-1.5"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                        {item.isResolved ? "Resolved" : "Mark as Mastered"}
                      </Button>

                      <Button
                        variant="tutor"
                        size="sm"
                        onClick={() =>
                          openSocraticDrawer({
                            topicTitle: item.topicTitle,
                            topicId: item.topicId,
                            questionStem: item.problemStemLatex,
                            studentAnswer: item.studentAnswer,
                          })
                        }
                        className="text-xs gap-1.5 font-bold"
                      >
                        <Sparkles className="h-3.5 w-3.5" /> Debug with Socratic AI
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
