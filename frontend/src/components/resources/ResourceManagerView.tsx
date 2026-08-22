import * as React from "react";
import { BookOpen } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ResourceCatalog } from "./ResourceCatalog";
import { ChapterIndex } from "./ChapterIndex";
import { DocumentReader } from "./DocumentReader";

export const ResourceManagerView: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in-50 duration-300">
      {/* 1. Header Banner */}
      <Card className="border-2 border-indigo-500/40 bg-gradient-to-br from-indigo-500/10 via-card to-card shadow-sm">
        <CardHeader className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Badge variant="masteryHigh" className="text-xs uppercase tracking-wider py-0.5 px-2.5">
                  Grounded Knowledge Retrieval
                </Badge>
                <span className="text-xs text-muted-foreground font-mono">
                  Verified Curriculum Library
                </span>
              </div>

              <CardTitle className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
                <BookOpen className="h-7 w-7 text-indigo-600 dark:text-indigo-400" />
                Curriculum Resource Hub & Grounded Reader
              </CardTitle>

              <CardDescription className="text-sm max-w-2xl">
                Inspect official endorsed coursebooks, syllabus learning specifications, and formula reference sheets with verified mathematical derivations and RAG citation provenance.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* 2. Top Resource Catalog & Search */}
      <ResourceCatalog />

      {/* 3. Document Reader Layout (Sidebar Index + Reader Stage) */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* Left 4 Cols: Chapter Index */}
        <div className="lg:col-span-4">
          <ChapterIndex />
        </div>

        {/* Right 8 Cols: Document Reader */}
        <div className="lg:col-span-8">
          <DocumentReader />
        </div>
      </div>
    </div>
  );
};
