import * as React from "react";
import { CheckCircle2, AlertCircle, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { TopicMasteryRecord } from "@/types/analytics";

export interface TopicMasteryListProps {
  topics: TopicMasteryRecord[];
}

export const TopicMasteryList: React.FC<TopicMasteryListProps> = ({ topics }) => {
  return (
    <div className="space-y-3.5">
      {topics.map((topic) => {
        const isMastered = topic.masteryTier === "Mastered";
        const isDeveloping = topic.masteryTier === "Developing";

        return (
          <div
            key={topic.topicId}
            className="rounded-xl border border-border/80 bg-card p-4 transition-all hover:border-border hover:shadow-xs space-y-2.5"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                  § {topic.syllabusCode}
                </span>
                <h4 className="text-sm font-bold text-foreground">
                  {topic.topicTitle}
                </h4>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[10px]">
                  {topic.bloomLevel}
                </Badge>

                <Badge
                  variant={
                    isMastered
                      ? "masteryHigh"
                      : isDeveloping
                      ? "masteryMedium"
                      : "masteryLow"
                  }
                  className="text-[10px]"
                >
                  {isMastered ? (
                    <CheckCircle2 className="h-3 w-3 mr-1 inline" />
                  ) : isDeveloping ? (
                    <Sparkles className="h-3 w-3 mr-1 inline" />
                  ) : (
                    <AlertCircle className="h-3 w-3 mr-1 inline" />
                  )}
                  {topic.masteryTier}
                </Badge>
              </div>
            </div>

            {/* Progress Bar & BKT Probabilities */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  Accuracy: <strong className="text-foreground">{topic.accuracyPercentage}%</strong> ({topic.correctCount}/{topic.totalAttempted})
                </span>
                <span className="font-mono text-[11px]">
                  BKT: <strong>{(topic.bktProbability * 100).toFixed(0)}%</strong> \(P(L_k)\)
                </span>
              </div>

              <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    topic.accuracyPercentage >= 80
                      ? "bg-emerald-500"
                      : topic.accuracyPercentage >= 50
                      ? "bg-amber-500"
                      : "bg-rose-500"
                  }`}
                  style={{ width: `${topic.accuracyPercentage}%` }}
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
