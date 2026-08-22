import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { AnalyticsState } from "@/types/analytics";
import {
  DEFAULT_STUDENT_SUMMARY,
  DEFAULT_TOPIC_MASTERY_RECORDS,
  DEFAULT_ERROR_BANK_ITEMS,
} from "@/api/analytics";

export const useAnalyticsStore = create<AnalyticsState>()(
  persist(
    (set) => ({
      summary: DEFAULT_STUDENT_SUMMARY,
      topicMasteryRecords: DEFAULT_TOPIC_MASTERY_RECORDS,
      errorBankItems: DEFAULT_ERROR_BANK_ITEMS,
      selectedCategoryFilter: "all",
      selectedTopicFilter: "all",

      setCategoryFilter: (category: string) =>
        set({ selectedCategoryFilter: category }),

      setTopicFilter: (topicId: string) =>
        set({ selectedTopicFilter: topicId }),

      resolveErrorItem: (itemId: string) =>
        set((state) => {
          const updatedItems = state.errorBankItems.map((item) =>
            item.id === itemId ? { ...item, isResolved: true } : item
          );
          const activeCount = updatedItems.filter((i) => !i.isResolved).length;
          const resolvedCount = updatedItems.filter((i) => i.isResolved).length;

          return {
            errorBankItems: updatedItems,
            summary: {
              ...state.summary,
              activeMisconceptionsCount: activeCount,
              resolvedErrorsCount: resolvedCount,
            },
          };
        }),

      resetAnalytics: () =>
        set({
          summary: DEFAULT_STUDENT_SUMMARY,
          topicMasteryRecords: DEFAULT_TOPIC_MASTERY_RECORDS,
          errorBankItems: DEFAULT_ERROR_BANK_ITEMS,
          selectedCategoryFilter: "all",
          selectedTopicFilter: "all",
        }),
    }),
    {
      name: "feynman_student_analytics_state",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        summary: state.summary,
        topicMasteryRecords: state.topicMasteryRecords,
        errorBankItems: state.errorBankItems,
        selectedCategoryFilter: state.selectedCategoryFilter,
        selectedTopicFilter: state.selectedTopicFilter,
      }),
    }
  )
);
