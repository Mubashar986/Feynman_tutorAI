import { apiClient } from "./client";

export interface DocumentResponse {
  id: string;
  exam_template_id?: string | null;
  topic_id?: string | null;
  title: string;
  original_filename: string;
  file_format: string;
  total_chunks: number;
  total_tokens: number;
  is_indexed: boolean;
  status: "pending" | "processing" | "chunked" | "indexed" | "failed";
  created_at: string;
  updated_at: string;
}

export interface DocumentChunkResponse {
  id: string;
  document_id: string;
  chunk_index: number;
  heading_breadcrumb?: string | null;
  text_content: string;
  token_count: number;
  is_formula_dense: boolean;
  created_at: string;
}

export interface RetrievedSourceCitation {
  chunk_id: string;
  document_id: string;
  document_title: string;
  topic_id?: string | null;
  topic_title?: string | null;
  heading_breadcrumb?: string | null;
  text_content: string;
  similarity_score: number;
  token_count: number;
}

export interface GroundedContextResponse {
  context_text: string;
  citations: RetrievedSourceCitation[];
  total_tokens: number;
  query: string;
}

export interface RetrievalQueryRequest {
  query: string;
  exam_template_id?: string | null;
  topic_id?: string | null;
  limit?: number;
  score_threshold?: number;
  max_context_tokens?: number;
}

// ==============================================================================
// Mock Data Fallbacks for Offline Dev & Testing
// ==============================================================================

export const MOCK_DOCUMENTS: DocumentResponse[] = [
  {
    id: "doc_physics_01",
    exam_template_id: "exam_alevel_01",
    topic_id: "top_kinematics_01",
    title: "University Physics: Classical Mechanics & Vectors",
    original_filename: "University_Physics_Ch02.pdf",
    file_format: "pdf",
    total_chunks: 14,
    total_tokens: 3850,
    is_indexed: true,
    status: "indexed",
    created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 3).toISOString(),
  },
  {
    id: "doc_physics_02",
    exam_template_id: "exam_alevel_01",
    topic_id: "top_optics_01",
    title: "Principles of Geometric & Wave Optics",
    original_filename: "Optics_Lecture_Notes.md",
    file_format: "md",
    total_chunks: 8,
    total_tokens: 2100,
    is_indexed: true,
    status: "indexed",
    created_at: new Date(Date.now() - 86400000 * 1).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 1).toISOString(),
  },
  {
    id: "doc_physics_03",
    exam_template_id: "exam_alevel_01",
    topic_id: "top_thermo_01",
    title: "Thermodynamics & Heat Engines Compendium",
    original_filename: "Thermo_Chapter_4.txt",
    file_format: "txt",
    total_chunks: 6,
    total_tokens: 1650,
    is_indexed: false,
    status: "chunked",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const MOCK_CHUNKS: Record<string, DocumentChunkResponse[]> = {
  doc_physics_01: [
    {
      id: "chk_01_01",
      document_id: "doc_physics_01",
      chunk_index: 0,
      heading_breadcrumb: "Chapter 2 > Kinematics in One Dimension > Average vs Instantaneous Velocity",
      text_content:
        "The instantaneous velocity $v(t)$ is defined as the mathematical derivative of position $x(t)$ with respect to time $t$:\n\n$$v(t) = \\lim_{\\Delta t \\to 0} \\frac{\\Delta x}{\\Delta t} = \\frac{dx}{dt}$$\n\nWhen acceleration $a$ is constant, the kinematic equations describe the exact trajectory without requiring direct integration at every step.",
      token_count: 78,
      is_formula_dense: true,
      created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    },
    {
      id: "chk_01_02",
      document_id: "doc_physics_01",
      chunk_index: 1,
      heading_breadcrumb: "Chapter 2 > Constant Acceleration Formulas > The Torricelli Equation",
      text_content:
        "By eliminating the time variable $t$ from the primary velocity and displacement equations, we derive Torricelli's equation for final velocity:\n\n$$v_f^2 = v_i^2 + 2a(x_f - x_i)$$\n\nThis scalar formulation is particularly useful in gravity problems where the total vertical displacement $\\Delta y$ is known but flight duration is unobserved.",
      token_count: 85,
      is_formula_dense: true,
      created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    },
  ],
};

// ==============================================================================
// Documents API Client
// ==============================================================================

export const documentsApi = {
  async listDocuments(
    examTemplateId?: string,
    topicId?: string,
    token?: string
  ): Promise<DocumentResponse[]> {
    const params = new URLSearchParams();
    if (examTemplateId) params.append("exam_template_id", examTemplateId);
    if (topicId) params.append("topic_id", topicId);

    const qs = params.toString() ? `?${params.toString()}` : "";
    try {
      return await apiClient<DocumentResponse[]>(`/api/v1/documents${qs}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch {
      return MOCK_DOCUMENTS.filter((d) => {
        if (examTemplateId && d.exam_template_id !== examTemplateId) return false;
        if (topicId && d.topic_id !== topicId) return false;
        return true;
      });
    }
  },

  async getDocument(documentId: string, token?: string): Promise<DocumentResponse> {
    try {
      return await apiClient<DocumentResponse>(`/api/v1/documents/${documentId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch {
      const match = MOCK_DOCUMENTS.find((d) => d.id === documentId);
      if (match) return match;
      throw new Error(`Document ${documentId} not found`);
    }
  },

  async getDocumentChunks(
    documentId: string,
    token?: string
  ): Promise<DocumentChunkResponse[]> {
    try {
      return await apiClient<DocumentChunkResponse[]>(
        `/api/v1/documents/${documentId}/chunks`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
    } catch {
      return MOCK_CHUNKS[documentId] || [
        {
          id: `chk_${documentId}_01`,
          document_id: documentId,
          chunk_index: 0,
          heading_breadcrumb: "Overview > Introduction",
          text_content: "This is a segmented semantic chunk from the curriculum source document.",
          token_count: 42,
          is_formula_dense: false,
          created_at: new Date().toISOString(),
        },
      ];
    }
  },

  async uploadDocument(
    formData: FormData,
    token?: string
  ): Promise<DocumentResponse> {
    try {
      return await apiClient<DocumentResponse>("/api/v1/documents/upload", {
        method: "POST",
        body: formData,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch {
      const file = formData.get("file") as File;
      const title = (formData.get("title") as string) || file?.name || "Uploaded Document";
      const topicId = formData.get("topic_id") as string;
      const examTemplateId = formData.get("exam_template_id") as string;

      const newDoc: DocumentResponse = {
        id: `doc_${Date.now().toString(36)}`,
        exam_template_id: examTemplateId || null,
        topic_id: topicId || null,
        title,
        original_filename: file?.name || "document.pdf",
        file_format: file?.name?.endsWith(".md") ? "md" : file?.name?.endsWith(".txt") ? "txt" : "pdf",
        total_chunks: 5,
        total_tokens: 1250,
        is_indexed: false,
        status: "chunked",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      MOCK_DOCUMENTS.unshift(newDoc);
      return newDoc;
    }
  },

  async deleteDocument(documentId: string, token?: string): Promise<void> {
    try {
      await apiClient<void>(`/api/v1/documents/${documentId}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch {
      const index = MOCK_DOCUMENTS.findIndex((d) => d.id === documentId);
      if (index !== -1) MOCK_DOCUMENTS.splice(index, 1);
    }
  },

  async indexDocument(
    documentId: string,
    token?: string
  ): Promise<{ document_id: string; status: string; chunks_indexed: number }> {
    try {
      return await apiClient<{ document_id: string; status: string; chunks_indexed: number }>(
        `/api/v1/documents/${documentId}/index`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
    } catch {
      const doc = MOCK_DOCUMENTS.find((d) => d.id === documentId);
      if (doc) {
        doc.is_indexed = true;
        doc.status = "indexed";
      }
      return {
        document_id: documentId,
        status: "indexed",
        chunks_indexed: doc?.total_chunks || 5,
      };
    }
  },

  async searchCurriculumSources(
    request: RetrievalQueryRequest,
    token?: string
  ): Promise<RetrievedSourceCitation[]> {
    try {
      return await apiClient<RetrievedSourceCitation[]>("/api/v1/documents/search", {
        method: "POST",
        body: JSON.stringify(request),
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
    } catch {
      return [
        {
          chunk_id: "chk_01_01",
          document_id: "doc_physics_01",
          document_title: "University Physics: Classical Mechanics",
          topic_id: "top_kinematics_01",
          topic_title: "Kinematics",
          heading_breadcrumb: "Chapter 2 > Kinematics in One Dimension",
          text_content:
            "The instantaneous velocity $v(t)$ is defined as the mathematical derivative of position $x(t)$ with respect to time $t$:\n\n$$v(t) = \\frac{dx}{dt}$$",
          similarity_score: 0.942,
          token_count: 78,
        },
        {
          chunk_id: "chk_01_02",
          document_id: "doc_physics_01",
          document_title: "University Physics: Classical Mechanics",
          topic_id: "top_kinematics_01",
          topic_title: "Kinematics",
          heading_breadcrumb: "Chapter 2 > Constant Acceleration Formulas",
          text_content:
            "Torricelli's kinematic equation relating velocities and displacement without time:\n\n$$v_f^2 = v_i^2 + 2a\\Delta x$$",
          similarity_score: 0.885,
          token_count: 85,
        },
      ];
    }
  },
};
