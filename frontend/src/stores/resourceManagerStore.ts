import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ResourceState, DocumentType } from "@/types/resource";
import { SAMPLE_CURRICULUM_DOCUMENTS } from "@/api/resources";

export const useResourceManagerStore = create<ResourceState>()(
  persist(
    (set) => ({
      documents: SAMPLE_CURRICULUM_DOCUMENTS,
      activeDocumentId: SAMPLE_CURRICULUM_DOCUMENTS[0].id,
      activeSectionId: SAMPLE_CURRICULUM_DOCUMENTS[0].sections[0].id,
      activeCitationSnippet: null,
      searchQuery: "",
      typeFilter: "all",

      setActiveDocument: (documentId: string) =>
        set((state) => {
          const doc = state.documents.find((d) => d.id === documentId);
          return {
            activeDocumentId: documentId,
            activeSectionId: doc && doc.sections.length > 0 ? doc.sections[0].id : null,
            activeCitationSnippet: null,
          };
        }),

      setActiveSection: (sectionId: string | null) =>
        set({ activeSectionId: sectionId }),

      setCitationHighlight: (documentId: string, sectionId: string, snippet: string) =>
        set({
          activeDocumentId: documentId,
          activeSectionId: sectionId,
          activeCitationSnippet: snippet,
        }),

      setSearchQuery: (query: string) =>
        set({ searchQuery: query }),

      setTypeFilter: (filter: DocumentType | "all") =>
        set({ typeFilter: filter }),

      resetView: () =>
        set({
          activeDocumentId: SAMPLE_CURRICULUM_DOCUMENTS[0].id,
          activeSectionId: SAMPLE_CURRICULUM_DOCUMENTS[0].sections[0].id,
          activeCitationSnippet: null,
          searchQuery: "",
          typeFilter: "all",
        }),
    }),
    {
      name: "feynman_resource_manager_state",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        activeDocumentId: state.activeDocumentId,
        activeSectionId: state.activeSectionId,
        typeFilter: state.typeFilter,
      }),
    }
  )
);
