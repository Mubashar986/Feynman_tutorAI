import { create } from "zustand";
import type { CurriculumState, Topic } from "@/types/curriculum";

export const useCurriculumStore = create<CurriculumState>((set) => ({
  activeExamId: "exam_cambridge_physics_9702",
  selectedTopic: null,
  searchQuery: "",
  expandedNodeIds: ["subj_mechanics", "subj_waves", "subj_calc_derivatives"],
  isDrawerOpen: false,

  setActiveExam: (examId: string) =>
    set({
      activeExamId: examId,
      selectedTopic: null,
      searchQuery: "",
      isDrawerOpen: false,
    }),

  setSelectedTopic: (topic: Topic | null) =>
    set({
      selectedTopic: topic,
      isDrawerOpen: topic !== null,
    }),

  setSearchQuery: (query: string) => set({ searchQuery: query }),

  toggleNode: (nodeId: string) =>
    set((state) => {
      const isExpanded = state.expandedNodeIds.includes(nodeId);
      return {
        expandedNodeIds: isExpanded
          ? state.expandedNodeIds.filter((id) => id !== nodeId)
          : [...state.expandedNodeIds, nodeId],
      };
    }),

  expandAll: (nodeIds: string[]) => set({ expandedNodeIds: nodeIds }),

  collapseAll: () => set({ expandedNodeIds: [] }),

  setIsDrawerOpen: (isOpen: boolean) => set({ isDrawerOpen: isOpen }),
}));
