import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { DAGState } from "@/types/dag";
import { SAMPLE_PHYSICS_DAG } from "@/api/dag";

export const useMisconceptionDAGStore = create<DAGState>()(
  persist(
    (set) => ({
      nodes: SAMPLE_PHYSICS_DAG.nodes,
      edges: SAMPLE_PHYSICS_DAG.edges,
      selectedNodeId: "topic_superposition", // Default to active misconception node
      zoomLevel: 1.0,
      filterMode: "all",

      selectNode: (nodeId: string | null) => set({ selectedNodeId: nodeId }),

      setZoomLevel: (zoom: number) => {
        const clamped = Math.max(0.6, Math.min(1.6, zoom));
        set({ zoomLevel: clamped });
      },

      setFilterMode: (mode: "all" | "misconceptions" | "critical_path") =>
        set({ filterMode: mode }),

      resetView: () =>
        set({
          nodes: SAMPLE_PHYSICS_DAG.nodes,
          edges: SAMPLE_PHYSICS_DAG.edges,
          selectedNodeId: "topic_superposition",
          zoomLevel: 1.0,
          filterMode: "all",
        }),
    }),
    {
      name: "feynman_misconception_dag_state",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        selectedNodeId: state.selectedNodeId,
        zoomLevel: state.zoomLevel,
        filterMode: state.filterMode,
      }),
    }
  )
);
