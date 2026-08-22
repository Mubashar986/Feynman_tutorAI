import * as React from "react";
import {
  CheckCircle2,
  AlertTriangle,
  Lock,
  Sparkles,
  ZoomIn,
  ZoomOut,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useMisconceptionDAGStore } from "@/stores/misconceptionDAGStore";
import type { DAGNode } from "@/types/dag";

export const MisconceptionDAGCanvas: React.FC = () => {
  const {
    nodes,
    edges,
    selectedNodeId,
    selectNode,
    zoomLevel,
    setZoomLevel,
    filterMode,
  } = useMisconceptionDAGStore();

  const nodeWidth = 190;
  const nodeHeight = 85;

  // Filter visible nodes based on mode
  const filteredNodes = nodes.filter((n) => {
    if (filterMode === "misconceptions") {
      return n.status === "misconception" || n.misconception !== undefined;
    }
    if (filterMode === "critical_path") {
      return n.status === "misconception" || n.status === "developing" || n.status === "locked";
    }
    return true;
  });

  const nodeMap = React.useMemo(() => {
    const map = new Map<string, DAGNode>();
    nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [nodes]);

  // Compute Cubic Bezier Spline paths for edges
  const edgePaths = React.useMemo(() => {
    return edges
      .map((edge) => {
        const source = nodeMap.get(edge.source);
        const target = nodeMap.get(edge.target);
        if (!source || !target) return null;

        const x0 = source.x + nodeWidth;
        const y0 = source.y + nodeHeight / 2;
        const x1 = target.x;
        const y1 = target.y + nodeHeight / 2;

        const dx = Math.abs(x1 - x0) * 0.5;
        const path = `M ${x0} ${y0} C ${x0 + dx} ${y0}, ${x1 - dx} ${y1}, ${x1} ${y1}`;

        const isSourceMisconception = source.status === "misconception";
        const isTargetLocked = target.status === "locked";

        return {
          id: edge.id,
          path,
          label: edge.label,
          labelX: (x0 + x1) / 2,
          labelY: (y0 + y1) / 2 - 8,
          isSourceMisconception,
          isTargetLocked,
        };
      })
      .filter(Boolean);
  }, [edges, nodeMap]);

  return (
    <div className="relative w-full rounded-2xl border border-border/80 bg-slate-950/5 dark:bg-slate-950/40 p-2 overflow-hidden shadow-inner min-h-[460px] flex items-center justify-center">
      {/* Zoom Control Overlay Toolbar */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-1 rounded-xl border bg-card/90 p-1 shadow-md backdrop-blur">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => setZoomLevel(zoomLevel + 0.15)}
          title="Zoom In"
          aria-label="Zoom In"
        >
          <ZoomIn className="h-3.5 w-3.5" />
        </Button>
        <span className="font-mono text-[10px] font-bold px-1.5 text-muted-foreground">
          {(zoomLevel * 100).toFixed(0)}%
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => setZoomLevel(zoomLevel - 0.15)}
          title="Zoom Out"
          aria-label="Zoom Out"
        >
          <ZoomOut className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => setZoomLevel(1.0)}
          title="Reset Zoom"
          aria-label="Reset Zoom"
        >
          <RotateCcw className="h-3 w-3" />
        </Button>
      </div>

      {/* SVG Canvas Stage */}
      <div className="w-full overflow-x-auto py-6 px-4 flex justify-center">
        <svg
          width={1050 * zoomLevel}
          height={440 * zoomLevel}
          viewBox="0 0 1050 440"
          className="overflow-visible select-none transition-transform duration-200"
          aria-label="Curriculum Misconception Directed Acyclic Graph"
        >
          <defs>
            {/* Standard Emerald/Mastered Arrow Marker */}
            <marker
              id="arrow-mastered"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" className="fill-emerald-500" />
            </marker>

            {/* Misconception Red Arrow Marker */}
            <marker
              id="arrow-misconception"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" className="fill-rose-500" />
            </marker>

            {/* Default Muted Arrow Marker */}
            <marker
              id="arrow-default"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" className="fill-slate-400" />
            </marker>
          </defs>

          {/* 1. Render Directed Edge Splines */}
          <g className="edges-layer">
            {edgePaths.map((edge) => {
              if (!edge) return null;
              return (
                <g key={edge.id} className="group">
                  <path
                    d={edge.path}
                    fill="none"
                    strokeWidth={edge.isSourceMisconception ? "2.5" : "2"}
                    className={`transition-colors ${
                      edge.isSourceMisconception
                        ? "stroke-rose-500/80 stroke-dasharray-4 animate-pulse"
                        : edge.isTargetLocked
                        ? "stroke-slate-300 dark:stroke-slate-700 stroke-dasharray-2"
                        : "stroke-emerald-500/60 dark:stroke-emerald-500/40"
                    }`}
                    markerEnd={`url(#${
                      edge.isSourceMisconception
                        ? "arrow-misconception"
                        : edge.isTargetLocked
                        ? "arrow-default"
                        : "arrow-mastered"
                    })`}
                  />
                  {edge.label && (
                    <text
                      x={edge.labelX}
                      y={edge.labelY}
                      textAnchor="middle"
                      className="fill-muted-foreground text-[9px] font-medium font-mono"
                    >
                      {edge.label}
                    </text>
                  )}
                </g>
              );
            })}
          </g>

          {/* 2. Render Interactive Topic Nodes */}
          <g className="nodes-layer">
            {filteredNodes.map((node) => {
              const isSelected = selectedNodeId === node.id;
              const isMastered = node.status === "mastered";
              const isDeveloping = node.status === "developing";
              const isMisconception = node.status === "misconception";

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  className="cursor-pointer transition-all"
                  onClick={() => selectNode(node.id)}
                  aria-label={`Topic node ${node.topicTitle}`}
                >
                  {/* Node Background Rect */}
                  <rect
                    width={nodeWidth}
                    height={nodeHeight}
                    rx="12"
                    className={`transition-all duration-300 ${
                      isSelected
                        ? "ring-2 ring-indigo-600 stroke-indigo-600 stroke-2 filter drop-shadow-md"
                        : ""
                    } ${
                      isMisconception
                        ? "fill-rose-500/10 stroke-rose-500/60 dark:fill-rose-500/15"
                        : isMastered
                        ? "fill-emerald-500/10 stroke-emerald-500/50 dark:fill-emerald-500/15"
                        : isDeveloping
                        ? "fill-amber-500/10 stroke-amber-500/50 dark:fill-amber-500/15"
                        : "fill-muted/30 stroke-border/80 opacity-70"
                    }`}
                  />

                  {/* Header Row: Syllabus Code & Status Icon */}
                  <text
                    x="12"
                    y="22"
                    className="font-mono text-[10px] font-bold fill-indigo-600 dark:fill-indigo-400"
                  >
                    § {node.syllabusCode}
                  </text>

                  {/* Status Indicator Icon */}
                  <g transform={`translate(${nodeWidth - 28}, 10)`}>
                    {isMastered ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                    ) : isMisconception ? (
                      <AlertTriangle className="h-4 w-4 text-rose-600 dark:text-rose-400 animate-bounce" />
                    ) : isDeveloping ? (
                      <Sparkles className="h-4 w-4 text-amber-500" />
                    ) : (
                      <Lock className="h-4 w-4 text-slate-400" />
                    )}
                  </g>

                  {/* Node Title (Truncated if long) */}
                  <text
                    x="12"
                    y="45"
                    className="fill-foreground font-bold text-xs tracking-tight"
                  >
                    {node.topicTitle.length > 22
                      ? `${node.topicTitle.slice(0, 20)}...`
                      : node.topicTitle}
                  </text>

                  {/* Accuracy & BKT Knowledge Pill */}
                  <g transform="translate(12, 58)">
                    <rect
                      width="76"
                      height="16"
                      rx="4"
                      className={`fill-background/80 stroke-border stroke-1`}
                    />
                    <text
                      x="38"
                      y="11"
                      textAnchor="middle"
                      className="text-[9px] font-mono font-bold fill-foreground"
                    >
                      {node.accuracyPercentage}% Acc
                    </text>

                    <rect
                      x="82"
                      width="60"
                      height="16"
                      rx="4"
                      className="fill-background/80 stroke-border stroke-1"
                    />
                    <text
                      x="112"
                      y="11"
                      textAnchor="middle"
                      className="text-[9px] font-mono fill-muted-foreground"
                    >
                      {(node.bktProbability * 100).toFixed(0)}% BKT
                    </text>
                  </g>
                </g>
              );
            })}
          </g>
        </svg>
      </div>
    </div>
  );
};
