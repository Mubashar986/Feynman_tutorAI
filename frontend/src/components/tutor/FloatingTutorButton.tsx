import * as React from "react";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSocraticTutorStore } from "@/stores/socraticTutorStore";

export const FloatingTutorButton: React.FC = () => {
  const { openDrawer, isOpen } = useSocraticTutorStore();

  if (isOpen) return null;

  return (
    <div className="fixed bottom-6 right-6 z-30">
      <Button
        variant="tutor"
        size="lg"
        onClick={() => openDrawer()}
        className="rounded-full shadow-xl shadow-indigo-500/25 px-4 py-3 gap-2 text-xs sm:text-sm font-bold animate-in fade-in-0 zoom-in-95 hover:scale-105 transition-all"
        aria-label="Open Socratic AI Tutor"
      >
        <Sparkles className="h-4 w-4" />
        <span className="hidden sm:inline">Ask Socratic AI</span>
      </Button>
    </div>
  );
};
