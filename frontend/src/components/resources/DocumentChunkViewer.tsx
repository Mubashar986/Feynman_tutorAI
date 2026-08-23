import React, { useEffect, useState } from "react";
import { X, BookOpen, Layers, Hash, Sparkles, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import { documentsApi, type DocumentChunkResponse, type DocumentResponse } from "@/api/documents";

interface DocumentChunkViewerProps {
  document: DocumentResponse;
  token?: string;
  onClose: () => void;
}

export const DocumentChunkViewer: React.FC<DocumentChunkViewerProps> = ({
  document,
  token,
  onClose,
}) => {
  const [chunks, setChunks] = useState<DocumentChunkResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterFormulaOnly, setFilterFormulaOnly] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadChunks() {
      try {
        setLoading(true);
        setError(null);
        const data = await documentsApi.getDocumentChunks(document.id, token);
        if (isMounted) {
          setChunks(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load document chunks");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadChunks();
    return () => {
      isMounted = false;
    };
  }, [document.id, token]);

  const displayedChunks = filterFormulaOnly
    ? chunks.filter((c) => c.is_formula_dense)
    : chunks;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl bg-card border-l border-border h-full flex flex-col shadow-2xl overflow-hidden"
        role="dialog"
        aria-label={`Chunk Inspector: ${document.title}`}
      >
        {/* Header */}
        <div className="p-5 border-b border-border bg-muted/40 flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground truncate max-w-md">
                {document.title}
              </h2>
            </div>
            <p className="text-xs text-muted-foreground flex items-center gap-3">
              <span>{document.original_filename}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Layers className="w-3.5 h-3.5" /> {chunks.length} Semantic Chunks
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Hash className="w-3.5 h-3.5" /> {document.total_tokens.toLocaleString()} Tokens
              </span>
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Close Inspector"
            className="hover:bg-muted"
          >
            <X className="w-5 h-5 text-muted-foreground" />
          </Button>
        </div>

        {/* Toolbar Filter */}
        <div className="px-5 py-3 border-b border-border/60 bg-muted/20 flex items-center justify-between text-xs">
          <span className="text-muted-foreground">
            Showing <strong className="text-foreground">{displayedChunks.length}</strong> of{" "}
            {chunks.length} chunks
          </span>
          <Button
            variant={filterFormulaOnly ? "secondary" : "outline"}
            size="sm"
            onClick={() => setFilterFormulaOnly(!filterFormulaOnly)}
            className="h-7 text-xs flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            {filterFormulaOnly ? "Showing Formula-Dense" : "Filter Formula-Dense"}
          </Button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {loading && (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground gap-3">
              <Loader2 className="w-7 h-7 animate-spin text-primary" />
              <p className="text-sm">Loading semantic chunks & LaTeX formulas...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-3 text-destructive text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && displayedChunks.length === 0 && (
            <div className="text-center py-16 text-muted-foreground">
              <Layers className="w-10 h-10 mx-auto mb-2 opacity-40" />
              <p className="text-sm font-medium">No chunks found matching current filter.</p>
            </div>
          )}

          {!loading &&
            !error &&
            displayedChunks.map((chunk) => (
              <div
                key={chunk.id}
                className="bg-card border border-border/80 rounded-xl p-4.5 shadow-sm space-y-3 hover:border-primary/40 transition-colors"
              >
                <div className="flex items-center justify-between text-xs border-b border-border/40 pb-2">
                  <span className="font-mono text-muted-foreground font-medium">
                    Chunk #{chunk.chunk_index + 1}
                  </span>
                  <div className="flex items-center gap-2">
                    {chunk.is_formula_dense && (
                      <Badge variant="outline" className="bg-cyan-950/40 text-cyan-400 border-cyan-800/60 text-[10px]">
                        Math / LaTeX
                      </Badge>
                    )}
                    <Badge variant="secondary" className="text-[10px]">
                      {chunk.token_count} Tokens
                    </Badge>
                  </div>
                </div>

                {chunk.heading_breadcrumb && (
                  <p className="text-xs font-medium text-cyan-400 bg-cyan-950/20 px-2.5 py-1 rounded border border-cyan-900/30 truncate">
                    {chunk.heading_breadcrumb}
                  </p>
                )}

                <div className="text-sm text-foreground/90 leading-relaxed font-sans prose prose-invert max-w-none">
                  <LaTeXRenderer content={chunk.text_content} />
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};
