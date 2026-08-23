import React, { useState } from "react";
import {
  FileText,
  Layers,
  Hash,
  Sparkles,
  Trash2,
  Database,
  Search,
  BookOpen,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { documentsApi, type DocumentResponse } from "@/api/documents";

interface DocumentGridProps {
  documents: DocumentResponse[];
  token?: string;
  isInstructorOrAdmin?: boolean;
  onInspectDocument: (document: DocumentResponse) => void;
  onRefresh: () => void;
}

export const DocumentGrid: React.FC<DocumentGridProps> = ({
  documents,
  token,
  isInstructorOrAdmin = true,
  onInspectDocument,
  onRefresh,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [indexingDocId, setIndexingDocId] = useState<string | null>(null);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);

  const handleIndexDocument = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    try {
      setIndexingDocId(docId);
      await documentsApi.indexDocument(docId, token);
      onRefresh();
    } finally {
      setIndexingDocId(null);
    }
  };

  const handleDeleteDocument = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this document and all its chunks?")) {
      return;
    }
    try {
      setDeletingDocId(docId);
      await documentsApi.deleteDocument(docId, token);
      onRefresh();
    } finally {
      setDeletingDocId(null);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = doc.title.toLowerCase().includes(q);
      const matchFile = doc.original_filename.toLowerCase().includes(q);
      if (!matchTitle && !matchFile) return false;
    }
    if (statusFilter === "indexed" && !doc.is_indexed) return false;
    if (statusFilter === "unindexed" && doc.is_indexed) return false;
    return true;
  });

  const getFormatBadgeColor = (format: string) => {
    switch (format.toLowerCase()) {
      case "pdf":
        return "bg-red-950/40 text-red-400 border-red-800/60";
      case "md":
        return "bg-cyan-950/40 text-cyan-400 border-cyan-800/60";
      default:
        return "bg-slate-950/40 text-slate-400 border-slate-800/60";
    }
  };

  return (
    <div className="space-y-5">
      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-card border border-border rounded-xl p-3.5 shadow-sm">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            type="text"
            placeholder="Search documents by title or filename..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs bg-background"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          <Filter className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 text-xs bg-background border border-border rounded-lg px-2.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="all">All Documents ({documents.length})</option>
            <option value="indexed">Indexed in Qdrant</option>
            <option value="unindexed">Pending Vector Index</option>
          </select>
        </div>
      </div>

      {/* Grid of Documents */}
      {filteredDocs.length === 0 ? (
        <div className="text-center py-16 bg-card border border-border rounded-2xl p-6 text-muted-foreground space-y-2">
          <BookOpen className="w-10 h-10 mx-auto opacity-40 text-muted-foreground" />
          <h4 className="text-sm font-semibold text-foreground">No documents found</h4>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto">
            {searchQuery || statusFilter !== "all"
              ? "No documents matched your current search or status filter."
              : "Upload a curriculum textbook, notes file, or syllabus PDF to start grounded tutoring."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4.5">
          {filteredDocs.map((doc) => (
            <div
              key={doc.id}
              onClick={() => onInspectDocument(doc)}
              className="group bg-card border border-border hover:border-primary/50 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer flex flex-col justify-between space-y-4"
            >
              {/* Header Card */}
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center text-primary flex-shrink-0 group-hover:scale-105 transition-transform">
                    <FileText className="w-4.5 h-4.5" />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Badge variant="outline" className={`text-[10px] uppercase font-mono px-2 py-0.5 ${getFormatBadgeColor(doc.file_format)}`}>
                      {doc.file_format}
                    </Badge>
                    {doc.is_indexed ? (
                      <Badge variant="outline" className="bg-emerald-950/40 text-emerald-400 border-emerald-800/60 text-[10px] flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Indexed
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-amber-950/40 text-amber-400 border-amber-800/60 text-[10px] flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Unindexed
                      </Badge>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2">
                    {doc.title}
                  </h3>
                  <p className="text-xs text-muted-foreground truncate mt-0.5">
                    {doc.original_filename}
                  </p>
                </div>
              </div>

              {/* Stats Footer */}
              <div className="space-y-3 pt-3 border-t border-border/40 text-xs">
                <div className="flex items-center justify-between text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5 text-cyan-400" /> {doc.total_chunks} Chunks
                  </span>
                  <span className="flex items-center gap-1 font-mono">
                    <Hash className="w-3.5 h-3.5 text-indigo-400" /> {doc.total_tokens.toLocaleString()} Tokens
                  </span>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between gap-2 pt-1">
                  <Button
                    variant="secondary"
                    size="sm"
                    className="h-8 text-xs flex-1 gap-1.5"
                    onClick={(e) => {
                      e.stopPropagation();
                      onInspectDocument(doc);
                    }}
                  >
                    <BookOpen className="w-3.5 h-3.5" /> Inspect Chunks
                  </Button>

                  {isInstructorOrAdmin && (
                    <div className="flex items-center gap-1">
                      {!doc.is_indexed && (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={indexingDocId === doc.id}
                          onClick={(e) => handleIndexDocument(e, doc.id)}
                          className="h-8 text-xs px-2.5 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/30 gap-1"
                          title="Generate embeddings and index into Qdrant"
                        >
                          {indexingDocId === doc.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Database className="w-3.5 h-3.5" />
                          )}
                          Index
                        </Button>
                      )}

                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={deletingDocId === doc.id}
                        onClick={(e) => handleDeleteDocument(e, doc.id)}
                        className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                        title="Delete Document"
                      >
                        {deletingDocId === doc.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
