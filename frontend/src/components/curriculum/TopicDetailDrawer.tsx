import * as React from "react";
import { Sparkles, Clock, Lock, Unlock, BookOpen, Layers } from "lucide-react";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerDescription, DrawerFooter, DrawerClose } from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import { useCurriculumStore } from "@/stores/curriculumStore";
import type { Topic } from "@/types/curriculum";

export interface TopicDetailDrawerProps {
  onStartPractice?: (topic: Topic) => void;
}

export const TopicDetailDrawer: React.FC<TopicDetailDrawerProps> = ({ onStartPractice }) => {
  const { selectedTopic, isDrawerOpen, setIsDrawerOpen } = useCurriculumStore();

  if (!selectedTopic) return null;

  return (
    <Drawer open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
      <DrawerContent className="max-h-[85vh] overflow-y-auto">
        <div className="mx-auto w-full max-w-2xl p-6 space-y-6">
          <DrawerHeader className="p-0 space-y-2 text-left">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Badge variant="socratic" className="text-xs capitalize">
                  {selectedTopic.difficulty}
                </Badge>
                <Badge variant="outline" className="text-xs gap-1">
                  <Clock className="h-3 w-3" /> {selectedTopic.estimatedHours} hrs
                </Badge>
              </div>
              <span className="text-xs text-muted-foreground font-mono">
                Topic ID: {selectedTopic.id}
              </span>
            </div>

            <DrawerTitle className="text-2xl font-bold tracking-tight text-foreground">
              {selectedTopic.title}
            </DrawerTitle>
            <DrawerDescription className="text-sm">
              {selectedTopic.description || "Master the key formulas, derivations, and diagnostic problem stems."}
            </DrawerDescription>
          </DrawerHeader>

          {/* Prerequisite Section */}
          <div className="rounded-lg border bg-muted/30 p-4 space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5" /> Prerequisite Dependencies
            </h4>
            {selectedTopic.prerequisites.length === 0 ? (
              <p className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 font-medium">
                <Unlock className="h-3.5 w-3.5" /> Foundational Entry Point — No prior prerequisites required.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2 pt-1">
                {selectedTopic.prerequisites.map((prereq) => (
                  <Badge
                    key={prereq.prerequisiteTopicId}
                    variant="masteryMedium"
                    className="gap-1.5 text-xs py-1"
                  >
                    <Lock className="h-3 w-3" /> Requires: {prereq.prerequisiteTopicTitle}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Learning Objectives List with KaTeX Math */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <BookOpen className="h-3.5 w-3.5" /> Syllabus Learning Objectives ({selectedTopic.objectives.length})
            </h4>

            <div className="space-y-3">
              {selectedTopic.objectives.map((obj) => (
                <div
                  key={obj.id}
                  className="rounded-lg border bg-card p-4 space-y-2 transition-all hover:border-border"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                      § {obj.code}
                    </span>
                    <Badge variant="outline" className="text-[10px]">
                      Bloom: {obj.bloomLevel}
                    </Badge>
                  </div>

                  <p className="text-sm leading-relaxed text-foreground">
                    {obj.description}
                  </p>

                  {obj.formulaLatex && (
                    <div className="rounded-md bg-muted/50 p-2.5 overflow-x-auto text-indigo-600 dark:text-indigo-400">
                      <LaTeXRenderer formula={obj.formulaLatex} displayMode={true} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <DrawerFooter className="p-0 pt-4 flex flex-col sm:flex-row gap-3">
            <Button
              variant="tutor"
              className="flex-1 gap-2"
              onClick={() => {
                setIsDrawerOpen(false);
                if (onStartPractice) onStartPractice(selectedTopic);
              }}
            >
              <Sparkles className="h-4 w-4" /> Practice Diagnostic Problem Set
            </Button>
            <DrawerClose asChild>
              <Button variant="outline">Close</Button>
            </DrawerClose>
          </DrawerFooter>
        </div>
      </DrawerContent>
    </Drawer>
  );
};
