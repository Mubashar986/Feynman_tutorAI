import * as React from "react";
import {
  Sparkles,
  ChevronLeft,
  ChevronRight,
  FileCheck,
  Zap,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import { FormattedMathText } from "@/components/tutor/ChatMessageBubble";
import { useResourceManagerStore } from "@/stores/resourceManagerStore";
import { useSocraticTutorStore } from "@/stores/socraticTutorStore";

export const DocumentReader: React.FC = () => {
  const {
    documents,
    activeDocumentId,
    activeSectionId,
    setActiveSection,
    activeCitationSnippet,
  } = useResourceManagerStore();

  const { openDrawer: openSocraticDrawer } = useSocraticTutorStore();

  const activeDoc = documents.find((d) => d.id === activeDocumentId) || documents[0];
  if (!activeDoc) return null;

  const currentSectionIdx = activeDoc.sections.findIndex((s) => s.id === activeSectionId);
  const activeSection =
    currentSectionIdx >= 0 ? activeDoc.sections[currentSectionIdx] : activeDoc.sections[0];

  if (!activeSection) return null;

  const handlePrevSection = () => {
    if (currentSectionIdx > 0) {
      setActiveSection(activeDoc.sections[currentSectionIdx - 1].id);
    }
  };

  const handleNextSection = () => {
    if (currentSectionIdx < activeDoc.sections.length - 1) {
      setActiveSection(activeDoc.sections[currentSectionIdx + 1].id);
    }
  };

  const handleAskTutor = () => {
    openSocraticDrawer({
      topicTitle: activeSection.title,
      topicId: activeSection.id,
      questionStem: `Exploring verified curriculum text: "${activeSection.title}" (§ ${activeSection.syllabusCode}) from ${activeDoc.title}.`,
    });
  };

  return (
    <Card className="border-border/80 shadow-xs">
      {/* 1. Document Page Header */}
      <CardHeader className="p-6 pb-4 border-b">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="masteryHigh" className="text-[10px]">
                § {activeSection.syllabusCode}
              </Badge>
              <span className="font-mono text-xs text-muted-foreground">
                Page {activeSection.pageNumber} of {activeDoc.totalPages}
              </span>
            </div>
            <CardTitle className="text-xl font-bold tracking-tight text-foreground">
              {activeSection.sectionNumber}. {activeSection.title}
            </CardTitle>
            <CardDescription className="text-xs">
              Source: <strong className="text-foreground">{activeDoc.title}</strong> ({activeDoc.edition})
            </CardDescription>
          </div>

          <Button
            variant="tutor"
            size="sm"
            onClick={handleAskTutor}
            className="self-start sm:self-auto gap-1.5 text-xs font-bold"
          >
            <Sparkles className="h-4 w-4" /> Ask Socratic Tutor
          </Button>
        </div>
      </CardHeader>

      {/* 2. Main Reader Content Body */}
      <CardContent className="p-6 space-y-6">
        {/* Verified RAG Citation Highlight Callout */}
        {activeSection.verifiedCitationSnippet && (
          <div
            className={`rounded-xl border p-4 transition-all ${
              activeCitationSnippet
                ? "border-amber-500 bg-amber-500/10 ring-2 ring-amber-500/30 shadow-xs"
                : "border-indigo-500/30 bg-indigo-500/5"
            }`}
          >
            <div className="flex items-center gap-2 text-xs font-bold text-indigo-700 dark:text-indigo-300">
              <FileCheck className="h-4 w-4 text-indigo-600" />
              <span>Verified Curriculum Source Passage:</span>
            </div>
            <div className="mt-2 text-xs italic leading-relaxed text-foreground">
              <FormattedMathText text={activeSection.verifiedCitationSnippet} />
            </div>
          </div>
        )}

        {/* Primary Reading Prose with Formatted KaTeX */}
        <div className="prose prose-sm dark:prose-invert max-w-none text-foreground leading-relaxed text-sm">
          <FormattedMathText text={activeSection.content} />
        </div>

        {/* Key Governing Formulas Box */}
        {activeSection.keyFormulas.length > 0 && (
          <div className="rounded-xl border border-border/80 bg-muted/30 p-4 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-foreground">
              <Zap className="h-4 w-4 text-amber-500" />
              <span>Key Governing Formulations:</span>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {activeSection.keyFormulas.map((formula, fIdx) => (
                <div
                  key={fIdx}
                  className="rounded-lg border bg-card p-2.5 text-center overflow-x-auto"
                >
                  <LaTeXRenderer formula={formula} displayMode={true} />
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>

      {/* 3. Footer Navigation Bar */}
      <CardFooter className="border-t p-4 flex items-center justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={handlePrevSection}
          disabled={currentSectionIdx <= 0}
          className="gap-1 text-xs"
        >
          <ChevronLeft className="h-4 w-4" /> Previous Section
        </Button>

        <span className="text-xs text-muted-foreground font-mono">
          Section {currentSectionIdx + 1} of {activeDoc.sections.length}
        </span>

        <Button
          variant="outline"
          size="sm"
          onClick={handleNextSection}
          disabled={currentSectionIdx >= activeDoc.sections.length - 1}
          className="gap-1 text-xs"
        >
          Next Section <ChevronRight className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
};
