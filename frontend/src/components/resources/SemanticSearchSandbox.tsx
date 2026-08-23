import React, { useState } from "react";
import { Search, Sparkles, BookOpen, Layers, Hash, ArrowRight, Loader2, Compass } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import { documentsApi, type RetrievedSourceCitation } from "@/api/documents";

interface SemanticSearchSandboxProps {
  examTemplateId?: string;
  topicId?: string;
  token?: string;
  onInspectDocument?: (documentId: string) => void;
}

export const SemanticSearchSandbox: React.FC<SemanticSearchSandboxProps> = ({
  examTemplateId,
  topicId,
  token,
  onInspectDocument,
}) => {
  const [query, setQuery] = useState("");
  const [citations, setCitations] = useState<RetrievedSourceCitation[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const sampleQueries = [
    "What is the derivation of Torricelli's kinematic equation?",
    "Explain Newton's second law in differential form with momentum",
    "How does Snell's law calculate refraction at a boundary?",
    "What is the efficiency of a Carnot heat engine?",
  ];

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    try {
      setLoading(true);
      setHasSearched(true);
      const results = await documentsApi.searchCurriculumSources(
        {
          query: searchQuery.trim(),
          exam_template_id: examTemplateId,
          topic_id: topicId,
          limit: 5,
          score_threshold: 0.60,
        },
        token
      );
      setCitations(results);
    } catch {
      setCitations([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Sandbox Hero */}
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-950/40 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
                Semantic Vector Search & Provenance Sandbox
                <Badge variant="outline" className="bg-cyan-950/30 text-cyan-400 border-cyan-800/50 text-[10px]">
                  Dense 384-D
                </Badge>
              </h3>
              <p className="text-xs text-muted-foreground">
                Query curriculum source embeddings directly to test retrieval relevance and inspect mathematical citations.
              </p>
            </div>
          </div>
        </div>

        {/* Query Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch(query);
          }}
          className="flex items-center gap-2.5"
        >
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3.5 top-1/2 -translate-y-1/2" />
            <Input
              type="text"
              placeholder="Ask any syllabus concept (e.g. 'How is angular momentum conserved in orbit?')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-10 bg-background/80 text-sm h-11 rounded-xl"
            />
          </div>
          <Button type="submit" disabled={!query.trim() || loading} className="h-11 px-5 rounded-xl gap-2 font-medium">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Retrieve
          </Button>
        </form>

        {/* Quick Sample Queries */}
        <div className="flex items-center gap-2 flex-wrap pt-1">
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-cyan-400" /> Try:
          </span>
          {sampleQueries.map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setQuery(sq);
                handleSearch(sq);
              }}
              className="text-xs bg-muted/40 hover:bg-muted text-muted-foreground hover:text-foreground px-2.5 py-1 rounded-lg border border-border/60 transition-colors text-left truncate max-w-xs"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Citations Results List */}
      <div className="space-y-4">
        {loading && (
          <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p className="text-sm font-medium">Vectorizing query & calculating cosine similarities...</p>
          </div>
        )}

        {!loading && hasSearched && citations.length === 0 && (
          <div className="text-center py-16 bg-card border border-border rounded-2xl p-6 text-muted-foreground space-y-2">
            <Search className="w-10 h-10 mx-auto opacity-40 text-muted-foreground" />
            <h4 className="text-sm font-semibold text-foreground">No source citations matched</h4>
            <p className="text-xs text-muted-foreground max-w-sm mx-auto">
              Try rephrasing your search query or lower the topic filters.
            </p>
          </div>
        )}

        {!loading &&
          citations.map((citation, index) => {
            const similarityPct = Math.round(citation.similarity_score * 100);
            return (
              <div
                key={citation.chunk_id || index}
                className="bg-card border border-border/80 hover:border-cyan-500/40 rounded-2xl p-5 shadow-sm space-y-3.5 transition-all duration-200"
              >
                {/* Citation Meta Bar */}
                <div className="flex items-center justify-between flex-wrap gap-2 text-xs border-b border-border/40 pb-2.5">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                    <span className="font-semibold text-foreground truncate max-w-xs">
                      {citation.document_title}
                    </span>
                    {citation.topic_title && (
                      <Badge variant="secondary" className="text-[10px]">
                        {citation.topic_title}
                      </Badge>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={`text-[11px] font-mono px-2 py-0.5 ${
                        similarityPct >= 90
                          ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/60"
                          : similarityPct >= 75
                          ? "bg-cyan-950/40 text-cyan-400 border-cyan-800/60"
                          : "bg-amber-950/40 text-amber-400 border-amber-800/60"
                      }`}
                    >
                      {similarityPct}% Similarity
                    </Badge>
                    <span className="text-muted-foreground flex items-center gap-1 font-mono text-[10px]">
                      <Hash className="w-3 h-3" /> {citation.token_count} Tok
                    </span>
                  </div>
                </div>

                {/* Heading Breadcrumb */}
                {citation.heading_breadcrumb && (
                  <p className="text-xs text-cyan-400/90 font-medium bg-cyan-950/20 px-3 py-1 rounded-md border border-cyan-900/30">
                    {citation.heading_breadcrumb}
                  </p>
                )}

                {/* Mathematical Passage Body */}
                <div className="text-sm text-foreground/90 leading-relaxed font-sans prose prose-invert max-w-none">
                  <LaTeXRenderer content={citation.text_content} />
                </div>

                {/* Jump to Source Action */}
                {onInspectDocument && (
                  <div className="flex justify-end pt-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onInspectDocument(citation.document_id)}
                      className="text-xs h-7 gap-1.5 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/30"
                    >
                      Inspect Full Document Chunks <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
};
