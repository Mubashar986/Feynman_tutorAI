import * as React from "react";
import {
  BookOpen,
  Search,
  FileText,
  Bookmark,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useResourceManagerStore } from "@/stores/resourceManagerStore";
import type { DocumentType } from "@/types/resource";

export const ResourceCatalog: React.FC = () => {
  const {
    documents,
    activeDocumentId,
    setActiveDocument,
    searchQuery,
    setSearchQuery,
    typeFilter,
    setTypeFilter,
  } = useResourceManagerStore();

  const filteredDocuments = documents.filter((doc) => {
    const matchesType = typeFilter === "all" || doc.type === typeFilter;
    const matchesSearch =
      searchQuery.trim() === "" ||
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.sections.some(
        (s) =>
          s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          s.syllabusCode.toLowerCase().includes(searchQuery.toLowerCase())
      );
    return matchesType && matchesSearch;
  });

  return (
    <div className="space-y-4">
      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search textbook chapters, formulas, or syllabus codes (§ 9702)..."
            className="pl-9 text-xs"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          {(
            [
              { id: "all", label: "All Resources" },
              { id: "coursebook", label: "Coursebooks" },
              { id: "formula_sheet", label: "Formula Sheets" },
              { id: "syllabus", label: "Syllabus Specs" },
            ] as { id: DocumentType | "all"; label: string }[]
          ).map((filter) => (
            <button
              key={filter.id}
              onClick={() => setTypeFilter(filter.id)}
              className={`rounded-full px-3 py-1 text-[11px] font-semibold transition-colors ${
                typeFilter === filter.id
                  ? "bg-indigo-600 text-white"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* Document Selection Grid */}
      <div className="grid gap-3 sm:grid-cols-3">
        {filteredDocuments.map((doc) => {
          const isSelected = activeDocumentId === doc.id;

          return (
            <div
              key={doc.id}
              onClick={() => setActiveDocument(doc.id)}
              className={`cursor-pointer rounded-xl border p-3.5 transition-all select-none ${
                isSelected
                  ? "border-indigo-600 bg-indigo-500/5 ring-1 ring-indigo-600 shadow-xs"
                  : "border-border/80 bg-card hover:bg-muted/20"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                      doc.type === "coursebook"
                        ? "bg-indigo-600 text-white"
                        : doc.type === "formula_sheet"
                        ? "bg-amber-600 text-white"
                        : "bg-emerald-600 text-white"
                    }`}
                  >
                    {doc.type === "coursebook" ? (
                      <BookOpen className="h-3.5 w-3.5" />
                    ) : doc.type === "formula_sheet" ? (
                      <FileText className="h-3.5 w-3.5" />
                    ) : (
                      <Bookmark className="h-3.5 w-3.5" />
                    )}
                  </div>
                  <div>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-muted-foreground block">
                      {doc.examBoard}
                    </span>
                    <h4 className="text-xs font-bold text-foreground line-clamp-1">
                      {doc.title}
                    </h4>
                  </div>
                </div>

                {isSelected && (
                  <Badge variant="masteryHigh" className="text-[9px] py-0 px-1.5">
                    Active
                  </Badge>
                )}
              </div>

              <p className="mt-2 text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                {doc.description}
              </p>

              <div className="mt-2.5 flex items-center justify-between text-[10px] text-muted-foreground border-t pt-2 font-mono">
                <span>{doc.totalPages} Pages</span>
                <span>{doc.sections.length} Sections</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
