import * as React from "react";
import type { TopicMasteryRecord } from "@/types/analytics";

export interface MasteryRadarChartProps {
  topics: TopicMasteryRecord[];
  size?: number;
}

export const MasteryRadarChart: React.FC<MasteryRadarChartProps> = ({
  topics,
  size = 360,
}) => {
  if (!topics || topics.length === 0) return null;

  const n = topics.length;
  const center = size / 2;
  const radius = size * 0.38;

  // Grid levels (20%, 40%, 60%, 80%, 100%)
  const levels = [0.2, 0.4, 0.6, 0.8, 1.0];

  // Helper to compute (x, y) given radius factor and index
  const getCoordinates = (factor: number, idx: number) => {
    const angle = (2 * Math.PI * idx) / n - Math.PI / 2;
    const r = radius * factor;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y, angle };
  };

  // Build points string for data polygon
  const dataPolygonPoints = topics
    .map((topic, i) => {
      const { x, y } = getCoordinates(topic.accuracyPercentage / 100, i);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="flex flex-col items-center justify-center p-2">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="overflow-visible select-none"
        aria-label="Student Mastery Radar Chart"
      >
        {/* Concentric Polygons */}
        {levels.map((level, lIdx) => {
          const points = Array.from({ length: n })
            .map((_, i) => {
              const { x, y } = getCoordinates(level, i);
              return `${x.toFixed(1)},${y.toFixed(1)}`;
            })
            .join(" ");

          return (
            <polygon
              key={lIdx}
              points={points}
              className="stroke-border/70 fill-muted/10 transition-colors"
              strokeWidth={lIdx === levels.length - 1 ? "1.5" : "0.75"}
            />
          );
        })}

        {/* Axis Spokes from center to outer vertices */}
        {topics.map((_, i) => {
          const { x, y } = getCoordinates(1.0, i);
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={x}
              y2={y}
              className="stroke-border/60"
              strokeWidth="1"
              strokeDasharray="3 3"
            />
          );
        })}

        {/* Student Mastery Filled Polygon */}
        <polygon
          points={dataPolygonPoints}
          className="fill-indigo-600/25 stroke-indigo-600 dark:fill-indigo-500/30 dark:stroke-indigo-400 transition-all duration-700 ease-out"
          strokeWidth="2.5"
          strokeLinejoin="round"
        />

        {/* Vertex Dots & Value Labels */}
        {topics.map((topic, i) => {
          const { x, y } = getCoordinates(topic.accuracyPercentage / 100, i);
          const labelPos = getCoordinates(1.18, i);

          const isMastered = topic.accuracyPercentage >= 80;
          const isMisconception = topic.accuracyPercentage < 50;

          return (
            <g key={topic.topicId} className="group cursor-default">
              {/* Vertex Dot */}
              <circle
                cx={x}
                cy={y}
                r="4.5"
                className={`transition-all ${
                  isMastered
                    ? "fill-emerald-500 stroke-background stroke-2"
                    : isMisconception
                    ? "fill-rose-500 stroke-background stroke-2"
                    : "fill-indigo-600 stroke-background stroke-2"
                }`}
              />

              {/* Topic Title Label */}
              <text
                x={labelPos.x}
                y={labelPos.y}
                textAnchor="middle"
                dominantBaseline="central"
                className="fill-foreground text-[10px] sm:text-[11px] font-semibold tracking-tight"
              >
                {topic.topicTitle.split(" ")[0]}
              </text>

              {/* Score Percentage Pill underneath title */}
              <text
                x={labelPos.x}
                y={labelPos.y + 11}
                textAnchor="middle"
                dominantBaseline="central"
                className={`text-[9px] font-mono font-bold ${
                  isMastered
                    ? "fill-emerald-600 dark:fill-emerald-400"
                    : isMisconception
                    ? "fill-rose-600 dark:fill-rose-400"
                    : "fill-indigo-600 dark:fill-indigo-400"
                }`}
              >
                {topic.accuracyPercentage}%
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
