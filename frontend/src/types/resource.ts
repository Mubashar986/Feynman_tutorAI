/**
 * TypeScript types for Curriculum Resource Management, Grounded Document Viewer, and RAG Provenance Highlights.
 */

export type DocumentType = "coursebook" | "syllabus" | "formula_sheet" | "notes";

export interface DocumentSection {
  id: string;
  sectionNumber: string;
  title: string;
  syllabusCode: string;
  pageNumber: number;
  content: string; // Formatted STEM text with Markdown and LaTeX ($...$, $$...$$)
  keyFormulas: string[];
  verifiedCitationSnippet?: string;
}

export interface CurriculumDocument {
  id: string;
  title: string;
  examBoard: string;
  type: DocumentType;
  author: string;
  edition: string;
  totalPages: number;
  description: string;
  sections: DocumentSection[];
}

export interface ResourceState {
  documents: CurriculumDocument[];
  activeDocumentId: string;
  activeSectionId: string | null;
  activeCitationSnippet: string | null;
  searchQuery: string;
  typeFilter: DocumentType | "all";

  // Actions
  setActiveDocument: (documentId: string) => void;
  setActiveSection: (sectionId: string | null) => void;
  setCitationHighlight: (documentId: string, sectionId: string, snippet: string) => void;
  setSearchQuery: (query: string) => void;
  setTypeFilter: (filter: DocumentType | "all") => void;
  resetView: () => void;
}
