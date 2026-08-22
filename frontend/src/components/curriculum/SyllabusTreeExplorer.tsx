import * as React from "react";
import {
  Search,
  ChevronDown,
  ChevronRight,
  BookOpen,
  Lock,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useCurriculumStore } from "@/stores/curriculumStore";
import { curriculumClient, CAMBRIDGE_PHYSICS_SUBJECTS, AP_CALCULUS_SUBJECTS } from "@/api/curriculum";
import type { Subject, Topic } from "@/types/curriculum";
import { TopicDetailDrawer } from "./TopicDetailDrawer";

export interface SyllabusTreeExplorerProps {
  onStartTopicPractice?: (topic: Topic) => void;
}

export const SyllabusTreeExplorer: React.FC<SyllabusTreeExplorerProps> = ({
  onStartTopicPractice,
}) => {
  const {
    activeExamId,
    searchQuery,
    setSearchQuery,
    expandedNodeIds,
    toggleNode,
    expandAll,
    collapseAll,
    setSelectedTopic,
  } = useCurriculumStore();

  const [subjects, setSubjects] = React.useState<Subject[]>(() => {
    return activeExamId === "exam_ap_calculus_bc"
      ? AP_CALCULUS_SUBJECTS
      : CAMBRIDGE_PHYSICS_SUBJECTS;
  });
  const [isLoading, setIsLoading] = React.useState<boolean>(false);

  React.useEffect(() => {
    let isMounted = true;
    curriculumClient.getSyllabusTree(activeExamId).then((data) => {
      if (isMounted) {
        setSubjects(data);
        setIsLoading(false);
      }
    });
    return () => {
      isMounted = false;
    };
  }, [activeExamId]);

  // Filter subjects and topics based on search query
  const filteredSubjects = React.useMemo(() => {
    if (!searchQuery.trim()) return subjects;
    const q = searchQuery.toLowerCase().trim();

    return subjects
      .map((subj) => {
        const subjectMatches = subj.title.toLowerCase().includes(q);
        const matchingTopics = subj.topics.filter(
          (topic) =>
            topic.title.toLowerCase().includes(q) ||
            topic.description?.toLowerCase().includes(q) ||
            topic.objectives.some(
              (o) =>
                o.description.toLowerCase().includes(q) ||
                o.code.toLowerCase().includes(q)
            )
        );

        if (subjectMatches || matchingTopics.length > 0) {
          return {
            ...subj,
            topics: subjectMatches ? subj.topics : matchingTopics,
          };
        }
        return null;
      })
      .filter((s): s is Subject => s !== null);
  }, [subjects, searchQuery]);

  const handleExpandAll = () => {
    expandAll(subjects.map((s) => s.id));
  };

  return (
    <div className="space-y-6">
      {/* Top Search & Actions Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search topics, formulas, or syllabus codes (e.g. Kinematics, 9702.4.1)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExpandAll}
            className="text-xs"
          >
            Expand All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={collapseAll}
            className="text-xs"
          >
            Collapse All
          </Button>
        </div>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-20 w-full animate-pulse rounded-xl border bg-muted/40"
            />
          ))}
        </div>
      )}

      {/* Empty Search State */}
      {!isLoading && filteredSubjects.length === 0 && (
        <div className="rounded-xl border border-dashed p-8 text-center space-y-3">
          <div className="mx-auto h-12 w-12 rounded-full bg-muted flex items-center justify-center text-muted-foreground">
            <Search className="h-6 w-6" />
          </div>
          <p className="text-sm font-semibold text-foreground">
            No syllabus topics match "{searchQuery}"
          </p>
          <p className="text-xs text-muted-foreground">
            Try searching for broader terms like "Waves", "Derivatives", or "Kinematics".
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSearchQuery("")}
            className="mt-2 text-xs"
          >
            Clear Search
          </Button>
        </div>
      )}

      {/* Subjects Tree Accordion List */}
      {!isLoading && (
        <div className="space-y-4">
          {filteredSubjects.map((subject) => {
            const isExpanded =
              expandedNodeIds.includes(subject.id) || searchQuery.trim().length > 0;

            return (
              <Card
                key={subject.id}
                className="overflow-hidden border-border/80 transition-all"
              >
                <CardHeader
                  className="cursor-pointer select-none bg-muted/20 p-4 transition-colors hover:bg-muted/40"
                  onClick={() => toggleNode(subject.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="text-muted-foreground">
                        {isExpanded ? (
                          <ChevronDown className="h-5 w-5" />
                        ) : (
                          <ChevronRight className="h-5 w-5" />
                        )}
                      </div>
                      <div>
                        <CardTitle className="text-base font-bold tracking-tight">
                          {subject.title}
                        </CardTitle>
                        <p className="text-xs text-muted-foreground">
                          {subject.description}
                        </p>
                      </div>
                    </div>

                    <Badge variant="outline" className="text-xs">
                      {subject.topics.length} Topics
                    </Badge>
                  </div>
                </CardHeader>

                {isExpanded && (
                  <CardContent className="p-4 pt-2 space-y-3">
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 pt-2">
                      {subject.topics.map((topic) => (
                        <div
                          key={topic.id}
                          className="group flex flex-col justify-between rounded-lg border bg-card p-4 transition-all hover:border-indigo-500/50 hover:shadow-sm"
                        >
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <Badge
                                variant={
                                  topic.difficulty === "foundational"
                                    ? "masteryHigh"
                                    : topic.difficulty === "intermediate"
                                    ? "masteryMedium"
                                    : "masteryLow"
                                }
                                className="text-[10px] capitalize"
                              >
                                {topic.difficulty}
                              </Badge>

                              <span className="text-[11px] text-muted-foreground flex items-center gap-1 font-medium">
                                <Clock className="h-3 w-3" /> {topic.estimatedHours}h
                              </span>
                            </div>

                            <h4 className="text-sm font-semibold leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                              {topic.title}
                            </h4>

                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {topic.description}
                            </p>
                          </div>

                          <div className="pt-4 space-y-2">
                            {/* Prerequisites Pill */}
                            {topic.prerequisites.length > 0 ? (
                              <div className="flex items-center gap-1 text-[11px] text-amber-600 dark:text-amber-400 font-medium">
                                <Lock className="h-3 w-3" />
                                <span>{topic.prerequisites.length} Prerequisite</span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-1 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                                <CheckCircle2 className="h-3 w-3" />
                                <span>Unlocked Entry Point</span>
                              </div>
                            )}

                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full justify-between text-xs group-hover:border-indigo-500/30"
                              onClick={() => setSelectedTopic(topic)}
                            >
                              <span>Inspect {topic.objectives.length} Objectives</span>
                              <BookOpen className="h-3.5 w-3.5 text-indigo-500" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Slide-over Objective Drawer */}
      <TopicDetailDrawer onStartPractice={onStartTopicPractice} />
    </div>
  );
};
