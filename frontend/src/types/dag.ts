/**
 * TypeScript types for the Interactive Misconception Directed Acyclic Graph (DAG).
 */

export type DAGNodeStatus = "mastered" | "developing" | "misconception" | "locked";

export interface DAGNodeMisconception {
  tag: string;
  detailLatex: string;
  adversarialPrompt: string;
}

export interface DAGNode {
  id: string;
  topicTitle: string;
  syllabusCode: string;
  x: number;
  y: number;
  accuracyPercentage: number;
  bktProbability: number;
  status: DAGNodeStatus;
  bloomLevel: "Recall" | "Application" | "Analysis" | "Evaluation";
  description: string;
  prerequisites: string[]; // List of topicIds
  unlocks: string[]; // List of topicIds
  misconception?: DAGNodeMisconception;
}

export interface DAGEdge {
  id: string;
  source: string; // source topicId
  target: string; // target topicId
  label?: string;
}

export interface DAGGraphData {
  examTemplateId: string;
  title: string;
  nodes: DAGNode[];
  edges: DAGEdge[];
}

export interface DAGState {
  nodes: DAGNode[];
  edges: DAGEdge[];
  selectedNodeId: string | null;
  zoomLevel: number; // 0.6 to 1.6
  filterMode: "all" | "misconceptions" | "critical_path";

  // Actions
  selectNode: (nodeId: string | null) => void;
  setZoomLevel: (zoom: number) => void;
  setFilterMode: (mode: "all" | "misconceptions" | "critical_path") => void;
  resetView: () => void;
}
