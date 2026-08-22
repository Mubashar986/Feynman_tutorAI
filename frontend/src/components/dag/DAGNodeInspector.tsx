import * as React from "react";
import {
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Lock,
  ShieldAlert,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import { useMisconceptionDAGStore } from "@/stores/misconceptionDAGStore";
import { useSocraticTutorStore } from "@/stores/socraticTutorStore";
import type { DAGNode } from "@/types/dag";

export const DAGNodeInspector: React.FC = () => {
  const { nodes, selectedNodeId } = useMisconceptionDAGStore();
  const { openDrawer: openSocraticDrawer, setMode: setSocraticMode } = useSocraticTutorStore();

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0];
  if (!selectedNode) return null;

  const nodeMap = new Map<string, DAGNode>();
  nodes.forEach((n) => nodeMap.set(n.id, n));

  const isMastered = selectedNode.status === "mastered";
  const isDeveloping = selectedNode.status === "developing";
  const isMisconception = selectedNode.status === "misconception";

  const handleLaunchAdversarial = () => {
    setSocraticMode("adversarial");
    openSocraticDrawer({
      topicTitle: selectedNode.topicTitle,
      topicId: selectedNode.id,
      questionStem:
        selectedNode.misconception?.adversarialPrompt ||
        `Let's stress-test your understanding of ${selectedNode.topicTitle}.`,
    });
  };

  const handleAskTutor = () => {
    setSocraticMode("socratic");
    openSocraticDrawer({
      topicTitle: selectedNode.topicTitle,
      topicId: selectedNode.id,
      questionStem: `Help me understand the prerequisites and core derivations of ${selectedNode.topicTitle}.`,
    });
  };

  return (
    <Card className="border-border/80 shadow-md">
      <CardHeader className="p-5 pb-3 border-b space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded-md">
            § {selectedNode.syllabusCode}
          </span>

          <Badge
            variant={
              isMastered
                ? "masteryHigh"
                : isDeveloping
                ? "masteryMedium"
                : isMisconception
                ? "destructive"
                : "secondary"
            }
            className="text-[10px] font-bold uppercase"
          >
            {isMastered ? (
              <CheckCircle2 className="h-3 w-3 mr-1 inline" />
            ) : isMisconception ? (
              <AlertTriangle className="h-3 w-3 mr-1 inline" />
            ) : isDeveloping ? (
              <Sparkles className="h-3 w-3 mr-1 inline" />
            ) : (
              <Lock className="h-3 w-3 mr-1 inline" />
            )}
            {selectedNode.status}
          </Badge>
        </div>

        <CardTitle className="text-lg font-bold text-foreground">
          {selectedNode.topicTitle}
        </CardTitle>
        <CardDescription className="text-xs leading-relaxed">
          {selectedNode.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="p-5 space-y-4 text-xs sm:text-sm">
        {/* Knowledge & Bloom Level Metrics */}
        <div className="grid grid-cols-2 gap-2 rounded-xl bg-muted/40 p-3 text-center">
          <div>
            <span className="block font-mono text-lg font-extrabold text-foreground">
              {selectedNode.accuracyPercentage}%
            </span>
            <span className="text-[10px] text-muted-foreground">Historical Accuracy</span>
          </div>
          <div>
            <span className="block font-mono text-lg font-extrabold text-indigo-600 dark:text-indigo-400">
              {(selectedNode.bktProbability * 100).toFixed(0)}%
            </span>
            <span className="text-[10px] text-muted-foreground">BKT Knowledge Tracing</span>
          </div>
        </div>

        {/* Diagnosed Misconception Warning Box */}
        {selectedNode.misconception && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/5 p-3.5 space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-rose-600 dark:text-rose-400 text-xs">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>Diagnosed Mental Model Contradiction:</span>
            </div>
            <p className="font-semibold text-foreground text-xs">
              {selectedNode.misconception.tag}
            </p>
            <div className="text-xs text-muted-foreground leading-relaxed">
              <LaTeXRenderer formula={selectedNode.misconception.detailLatex} />
            </div>
          </div>
        )}

        {/* Prerequisite Lineage */}
        <div className="space-y-2 pt-1 border-t">
          <span className="font-bold text-[11px] uppercase tracking-wider text-muted-foreground block">
            Prerequisite Dependency Chain:
          </span>

          <div className="space-y-1.5 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-muted-foreground min-w-[70px]">Requires:</span>
              {selectedNode.prerequisites.length === 0 ? (
                <span className="text-muted-foreground italic">None (Foundational Entry Point)</span>
              ) : (
                <div className="flex flex-wrap gap-1">
                  {selectedNode.prerequisites.map((pId) => {
                    const req = nodeMap.get(pId);
                    return (
                      <Badge key={pId} variant="outline" className="text-[10px]">
                        § {req?.syllabusCode || pId}
                      </Badge>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <span className="font-semibold text-muted-foreground min-w-[70px]">Unlocks:</span>
              {selectedNode.unlocks.length === 0 ? (
                <span className="text-muted-foreground italic">Terminal Exam Skill</span>
              ) : (
                <div className="flex flex-wrap gap-1">
                  {selectedNode.unlocks.map((uId) => {
                    const unl = nodeMap.get(uId);
                    return (
                      <Badge key={uId} variant="outline" className="text-[10px]">
                        § {unl?.syllabusCode || uId}
                      </Badge>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex flex-col gap-2 border-t p-4 bg-muted/10">
        {selectedNode.misconception && (
          <Button
            variant="destructive"
            size="sm"
            onClick={handleLaunchAdversarial}
            className="w-full gap-1.5 font-bold text-xs shadow-xs"
          >
            <ShieldAlert className="h-4 w-4" /> Launch Adversarial Challenge
          </Button>
        )}

        <Button
          variant="tutor"
          size="sm"
          onClick={handleAskTutor}
          className="w-full gap-1.5 font-semibold text-xs"
        >
          <Sparkles className="h-3.5 w-3.5" /> Ask Socratic AI Tutor
        </Button>
      </CardFooter>
    </Card>
  );
};
