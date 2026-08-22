import * as React from "react";
import { Clock, AlertTriangle, Flame } from "lucide-react";
import { useExamPlayerStore } from "@/stores/examPlayerStore";

export const ExamTimer: React.FC = () => {
  const { timeRemainingSeconds, tickTimer, isSubmitted } = useExamPlayerStore();

  React.useEffect(() => {
    if (isSubmitted || timeRemainingSeconds <= 0) return;

    const interval = setInterval(() => {
      tickTimer();
    }, 1000);

    return () => clearInterval(interval);
  }, [isSubmitted, timeRemainingSeconds, tickTimer]);

  const minutes = Math.floor(timeRemainingSeconds / 60);
  const seconds = timeRemainingSeconds % 60;
  const formattedTime = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  // Timer urgency levels
  const isCritical = timeRemainingSeconds > 0 && timeRemainingSeconds <= 60;
  const isWarning = timeRemainingSeconds > 60 && timeRemainingSeconds <= 300;

  return (
    <div
      aria-label="Exam Time Remaining"
      className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 font-mono text-xs font-bold transition-all shadow-sm ${
        isCritical
          ? "border-rose-600 bg-rose-500/15 text-rose-600 dark:text-rose-400 animate-pulse ring-2 ring-rose-500/30"
          : isWarning
          ? "border-amber-500 bg-amber-500/10 text-amber-600 dark:text-amber-400"
          : "border-border bg-card text-foreground"
      }`}
    >
      {isCritical ? (
        <Flame className="h-4 w-4 text-rose-600 dark:text-rose-400 animate-bounce" />
      ) : isWarning ? (
        <AlertTriangle className="h-4 w-4 text-amber-500" />
      ) : (
        <Clock className="h-4 w-4 text-indigo-500" />
      )}
      <span className="tracking-wider">{formattedTime}</span>
    </div>
  );
};
