import * as React from "react";
import { ListOrdered, ChevronRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useResourceManagerStore } from "@/stores/resourceManagerStore";

export const ChapterIndex: React.FC = () => {
  const { documents, activeDocumentId, activeSectionId, setActiveSection } =
    useResourceManagerStore();

  const activeDoc = documents.find((d) => d.id === activeDocumentId) || documents[0];
  if (!activeDoc) return null;

  return (
    <Card className="border-border/80 shadow-xs h-full">
      <CardHeader className="p-4 pb-3 border-b">
        <CardTitle className="text-xs font-bold flex items-center gap-2 text-foreground">
          <ListOrdered className="h-4 w-4 text-indigo-600" />
          Table of Contents ({activeDoc.sections.length})
        </CardTitle>
      </CardHeader>

      <CardContent className="p-2 space-y-1 overflow-y-auto max-h-[550px]">
        {activeDoc.sections.map((section) => {
          const isActive = activeSectionId === section.id;

          return (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`w-full text-left rounded-lg p-2.5 transition-all text-xs flex items-center justify-between gap-2 ${
                isActive
                  ? "bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 font-bold border border-indigo-500/30"
                  : "text-muted-foreground hover:bg-muted/40 hover:text-foreground"
              }`}
            >
              <div className="space-y-0.5 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-[10px] font-bold text-muted-foreground">
                    § {section.sectionNumber}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    p. {section.pageNumber}
                  </span>
                </div>
                <p className="font-semibold text-foreground truncate text-xs">
                  {section.title}
                </p>
              </div>

              <ChevronRight
                className={`h-3.5 w-3.5 shrink-0 ${
                  isActive ? "text-indigo-600" : "text-muted-foreground opacity-40"
                }`}
              />
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
};
