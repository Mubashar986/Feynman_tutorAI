import * as React from "react";
import { Atom, Binary, Calculator, CheckCircle2, ArrowRight, BookOpen, Layers } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useCurriculumStore } from "@/stores/curriculumStore";
import { EXAM_CATALOG } from "@/api/curriculum";

export interface ExamCatalogGridProps {
  onSelectExam?: (examId: string) => void;
}

export const ExamCatalogGrid: React.FC<ExamCatalogGridProps> = ({ onSelectExam }) => {
  const { activeExamId, setActiveExam } = useCurriculumStore();

  const getExamIcon = (iconName: string) => {
    switch (iconName) {
      case "Atom":
        return <Atom className="h-6 w-6 text-indigo-500" />;
      case "Binary":
        return <Binary className="h-6 w-6 text-emerald-500" />;
      case "Calculator":
        return <Calculator className="h-6 w-6 text-amber-500" />;
      default:
        return <BookOpen className="h-6 w-6 text-indigo-500" />;
    }
  };

  const handleSelect = (examId: string) => {
    setActiveExam(examId);
    if (onSelectExam) onSelectExam(examId);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Curriculum Blueprint Catalog</h2>
          <p className="text-sm text-muted-foreground">
            Select your target examination to explore the complete syllabus hierarchy and prerequisite dependency tree.
          </p>
        </div>
        <Badge variant="outline" className="self-start sm:self-auto gap-1">
          <Layers className="h-3 w-3" /> {EXAM_CATALOG.length} Standard Blueprints
        </Badge>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {EXAM_CATALOG.map((exam) => {
          const isActive = activeExamId === exam.id;

          return (
            <Card
              key={exam.id}
              className={`flex flex-col justify-between transition-all hover:shadow-md ${
                isActive
                  ? "border-indigo-600 ring-2 ring-indigo-500/20 bg-indigo-500/5 dark:bg-indigo-950/10"
                  : "border-border/80 hover:border-border"
              }`}
            >
              <CardHeader className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="h-12 w-12 rounded-xl bg-card border shadow-sm flex items-center justify-center">
                    {getExamIcon(exam.iconName)}
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <Badge variant="secondary" className="text-[11px] font-mono">
                      Code: {exam.code}
                    </Badge>
                    <Badge variant="outline" className="text-[10px]">
                      {exam.board}
                    </Badge>
                  </div>
                </div>

                <div>
                  <CardTitle className="text-lg font-bold leading-snug">{exam.title}</CardTitle>
                  <CardDescription className="text-xs line-clamp-2 mt-1">
                    {exam.description}
                  </CardDescription>
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                <div className="grid grid-cols-3 gap-2 rounded-lg bg-muted/40 p-2.5 text-center text-xs">
                  <div>
                    <span className="block font-bold text-foreground">{exam.subjectCount}</span>
                    <span className="text-[10px] text-muted-foreground">Subjects</span>
                  </div>
                  <div>
                    <span className="block font-bold text-foreground">{exam.topicCount}</span>
                    <span className="text-[10px] text-muted-foreground">Topics</span>
                  </div>
                  <div>
                    <span className="block font-bold text-foreground">{exam.objectiveCount}</span>
                    <span className="text-[10px] text-muted-foreground">Objectives</span>
                  </div>
                </div>

                <div className="text-xs text-muted-foreground flex items-center justify-between">
                  <span>Level:</span>
                  <span className="font-semibold text-foreground">{exam.difficultyLevel}</span>
                </div>
              </CardContent>

              <CardFooter className="pt-2">
                <Button
                  variant={isActive ? "mastery" : "outline"}
                  className="w-full justify-between text-xs"
                  onClick={() => handleSelect(exam.id)}
                >
                  <span>{isActive ? "Active Syllabus Target" : "Select & Explore Syllabus"}</span>
                  {isActive ? <CheckCircle2 className="h-4 w-4" /> : <ArrowRight className="h-4 w-4" />}
                </Button>
              </CardFooter>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
