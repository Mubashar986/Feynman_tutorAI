import React, { useEffect, useState } from "react";
import {
  BookOpen,
  UploadCloud,
  Compass,
  Layers,
  Hash,
  Database,
  RefreshCw,
  Plus,
  Loader2,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { documentsApi, type DocumentResponse } from "@/api/documents";
import { DocumentGrid } from "./DocumentGrid";
import { DocumentUploadModal } from "./DocumentUploadModal";
import { DocumentChunkViewer } from "./DocumentChunkViewer";
import { SemanticSearchSandbox } from "./SemanticSearchSandbox";

interface ResourceManagerViewProps {
  examTemplateId?: string;
  topicId?: string;
  token?: string;
  userRole?: string;
}

export const ResourceManagerView: React.FC<ResourceManagerViewProps> = ({
  examTemplateId,
  topicId,
  token,
  userRole = "student",
}) => {
  const [activeTab, setActiveTab] = useState<"library" | "sandbox">("library");
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [selectedInspectDoc, setSelectedInspectDoc] = useState<DocumentResponse | null>(null);

  const isInstructorOrAdmin =
    userRole === "instructor" || userRole === "admin" || userRole === "content_admin";

  const fetchDocuments = async () => {
    try {
      setRefreshing(true);
      const docs = await documentsApi.listDocuments(examTemplateId, topicId, token);
      setDocuments(docs);
    } catch {
      // Handled by api client fallback
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [examTemplateId, topicId, token]);

  const totalTokens = documents.reduce((acc, d) => acc + (d.total_tokens || 0), 0);
  const totalChunks = documents.reduce((acc, d) => acc + (d.total_chunks || 0), 0);
  const indexedCount = documents.filter((d) => d.is_indexed).length;

  const handleInspectDocumentById = (docId: string) => {
    const targetDoc = documents.find((d) => d.id === docId);
    if (targetDoc) {
      setSelectedInspectDoc(targetDoc);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 animate-in fade-in duration-300">
      {/* Top Header Hero */}
      <div className="bg-gradient-to-r from-card via-card to-muted/20 border border-border rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                Curriculum Library & Resource Manager
                <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30 text-[11px]">
                  RAG Knowledge Base
                </Badge>
              </h1>
              <p className="text-xs text-muted-foreground">
                Grounded textbooks, lecture notes, and syllabus PDFs segmented with LaTeX formula preservation (PRD FR-008).
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchDocuments}
            disabled={refreshing}
            className="h-9 gap-1.5 text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          {isInstructorOrAdmin && (
            <Button
              size="sm"
              onClick={() => setIsUploadModalOpen(true)}
              className="h-9 gap-1.5 text-xs bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
            >
              <Plus className="w-4 h-4" />
              Upload Source Document
            </Button>
          )}
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className="bg-card border border-border/80 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-950/40 border border-blue-800/60 flex items-center justify-center text-blue-400">
            <BookOpen className="w-4.5 h-4.5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total Documents</p>
            <p className="text-lg font-bold text-foreground">{documents.length}</p>
          </div>
        </div>

        <div className="bg-card border border-border/80 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-950/40 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <Layers className="w-4.5 h-4.5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Semantic Chunks</p>
            <p className="text-lg font-bold text-foreground">{totalChunks.toLocaleString()}</p>
          </div>
        </div>

        <div className="bg-card border border-border/80 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-950/40 border border-indigo-800/60 flex items-center justify-center text-indigo-400">
            <Hash className="w-4.5 h-4.5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Indexed Tokens</p>
            <p className="text-lg font-bold text-foreground">{totalTokens.toLocaleString()}</p>
          </div>
        </div>

        <div className="bg-card border border-border/80 rounded-xl p-4 shadow-sm flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-950/40 border border-emerald-800/60 flex items-center justify-center text-emerald-400">
            <Database className="w-4.5 h-4.5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Vector Status</p>
            <p className="text-sm font-semibold text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> {indexedCount}/{documents.length} Indexed
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-1">
        <button
          type="button"
          onClick={() => setActiveTab("library")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
            activeTab === "library"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          Document Library ({documents.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("sandbox")}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
            activeTab === "sandbox"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          Semantic Search Sandbox
        </button>
      </div>

      {/* Main Tab Content Area */}
      {activeTab === "library" ? (
        loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p className="text-sm font-medium">Loading curriculum source documents...</p>
          </div>
        ) : (
          <DocumentGrid
            documents={documents}
            token={token}
            isInstructorOrAdmin={isInstructorOrAdmin}
            onInspectDocument={(doc) => setSelectedInspectDoc(doc)}
            onRefresh={fetchDocuments}
          />
        )
      ) : (
        <SemanticSearchSandbox
          examTemplateId={examTemplateId}
          topicId={topicId}
          token={token}
          onInspectDocument={handleInspectDocumentById}
        />
      )}

      {/* Upload Modal */}
      {isUploadModalOpen && (
        <DocumentUploadModal
          examTemplateId={examTemplateId}
          topicId={topicId}
          token={token}
          onClose={() => setIsUploadModalOpen(false)}
          onSuccess={() => {
            fetchDocuments();
          }}
        />
      )}

      {/* Chunk Inspector Drawer */}
      {selectedInspectDoc && (
        <DocumentChunkViewer
          document={selectedInspectDoc}
          token={token}
          onClose={() => setSelectedInspectDoc(null)}
        />
      )}
    </div>
  );
};
