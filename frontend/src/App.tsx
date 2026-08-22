import * as React from "react";
import {
  GraduationCap,
  Sparkles,
  Moon,
  Sun,
  Layers,
  LogIn,
  UserCheck,
  FolderTree,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useAuthStore } from "@/stores/authStore";
import { LoginForm } from "@/components/auth/LoginForm";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { UserProfileMenu } from "@/components/auth/UserProfileMenu";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { ExamCatalogGrid } from "@/components/curriculum/ExamCatalogGrid";
import { SyllabusTreeExplorer } from "@/components/curriculum/SyllabusTreeExplorer";
import { ExamPlayer } from "@/components/exam/ExamPlayer";
import { AnalyticsDashboard } from "@/components/analytics/AnalyticsDashboard";
import { useCurriculumStore } from "@/stores/curriculumStore";
import { SocraticTutorDrawer } from "@/components/tutor/SocraticTutorDrawer";
import { FloatingTutorButton } from "@/components/tutor/FloatingTutorButton";
import { useSocraticTutorStore } from "@/stores/socraticTutorStore";

export function App() {
  const [isDark, setIsDark] = React.useState<boolean>(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = React.useState<boolean>(false);
  const [authView, setAuthView] = React.useState<"login" | "register">("login");
  const [activeTab, setActiveTab] = React.useState<"catalog" | "syllabus" | "solver" | "analytics">("syllabus");

  const { user, isAuthenticated } = useAuthStore();
  const { activeExamId } = useCurriculumStore();
  const { openDrawer: openSocraticDrawer } = useSocraticTutorStore();

  const toggleDarkMode = () => {
    setIsDark((prev) => {
      const next = !prev;
      if (next) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      return next;
    });
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background text-foreground transition-colors duration-200">
        {/* Top Navigation Bar */}
        <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-md">
                <GraduationCap className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-lg font-bold tracking-tight">Feynman Tutor AI</h1>
                <p className="text-xs text-muted-foreground">Adaptive Exam Learning Platform</p>
              </div>
            </div>

            {/* Navigation Tabs Switcher */}
            <div className="hidden md:flex items-center gap-1 rounded-lg border bg-muted/40 p-1 text-xs">
              <button
                onClick={() => setActiveTab("catalog")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                  activeTab === "catalog"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Layers className="h-3.5 w-3.5" /> Exam Catalog
              </button>
              <button
                onClick={() => setActiveTab("syllabus")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                  activeTab === "syllabus"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <FolderTree className="h-3.5 w-3.5" /> Syllabus Tree
              </button>
              <button
                onClick={() => setActiveTab("solver")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                  activeTab === "solver"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Sparkles className="h-3.5 w-3.5 text-indigo-500" /> Interactive Exam Player
              </button>
              <button
                onClick={() => setActiveTab("analytics")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                  activeTab === "analytics"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <BarChart3 className="h-3.5 w-3.5 text-emerald-500" /> Analytics & Errors
              </button>
            </div>

            <div className="flex items-center gap-3">
              {isAuthenticated && user ? (
                <UserProfileMenu />
              ) : (
                <Button
                  variant="tutor"
                  size="sm"
                  className="gap-1.5"
                  onClick={() => {
                    setAuthView("login");
                    setIsAuthModalOpen(true);
                  }}
                >
                  <LogIn className="h-4 w-4" /> Sign In
                </Button>
              )}

              <Button
                variant="outline"
                size="icon"
                onClick={toggleDarkMode}
                aria-label="Toggle theme"
              >
                {isDark ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-slate-700" />}
              </Button>
            </div>
          </div>
        </header>

        {/* Mobile Navigation Tabs */}
        <div className="flex md:hidden border-b bg-muted/20 px-2 py-2 justify-center gap-1 text-[11px] overflow-x-auto">
          <button
            onClick={() => setActiveTab("catalog")}
            className={`px-2.5 py-1 rounded-md shrink-0 ${activeTab === "catalog" ? "bg-card font-bold shadow-sm" : "text-muted-foreground"}`}
          >
            Catalog
          </button>
          <button
            onClick={() => setActiveTab("syllabus")}
            className={`px-2.5 py-1 rounded-md shrink-0 ${activeTab === "syllabus" ? "bg-card font-bold shadow-sm" : "text-muted-foreground"}`}
          >
            Syllabus
          </button>
          <button
            onClick={() => setActiveTab("solver")}
            className={`px-2.5 py-1 rounded-md shrink-0 ${activeTab === "solver" ? "bg-card font-bold shadow-sm" : "text-muted-foreground"}`}
          >
            Exam Player
          </button>
          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-2.5 py-1 rounded-md shrink-0 ${activeTab === "analytics" ? "bg-card font-bold shadow-sm" : "text-muted-foreground"}`}
          >
            Analytics
          </button>
        </div>

        {/* Auth Dialog Modal */}
        <Dialog open={isAuthModalOpen} onOpenChange={setIsAuthModalOpen}>
          <DialogContent className="sm:max-w-md p-0 overflow-hidden border-0 bg-transparent shadow-none">
            {authView === "login" ? (
              <LoginForm
                onSuccess={() => setIsAuthModalOpen(false)}
                onSwitchToRegister={() => setAuthView("register")}
              />
            ) : (
              <RegisterForm
                onSuccess={() => setIsAuthModalOpen(false)}
                onSwitchToLogin={() => setAuthView("login")}
              />
            )}
          </DialogContent>
        </Dialog>

        {/* Main Content */}
        <main className="container max-w-7xl px-4 py-8 sm:px-8 space-y-8">
          {/* Personalized Hero Banner */}
          <section className="space-y-3 text-center sm:text-left">
            <div className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground bg-muted/50">
              <Layers className="h-3.5 w-3.5 text-indigo-500" />
              {isAuthenticated ? (
                <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                  <UserCheck className="h-3.5 w-3.5" /> Authenticated Session Active
                </span>
              ) : (
                "Task 5.3: Adaptive Mastery Engine & Knowledge Tracing"
              )}
            </div>

            <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
              {isAuthenticated && user ? (
                <>Welcome back, <span className="text-indigo-600 dark:text-indigo-400">{user.fullName}</span></>
              ) : (
                "Curriculum-Grounded Adaptive Learning"
              )}
            </h2>

            <p className="max-w-3xl text-muted-foreground leading-relaxed text-sm sm:text-base">
              Inspect multi-axis mastery radar profiles, review diagnosed misconceptions in your Error Bank, and simulate real proctored exams.
            </p>
          </section>

          {/* TAB 1: Exam Template Catalog */}
          {activeTab === "catalog" && (
            <section className="space-y-6">
              <ExamCatalogGrid onSelectExam={() => setActiveTab("syllabus")} />
            </section>
          )}

          {/* TAB 2: Syllabus Tree Explorer */}
          {activeTab === "syllabus" && (
            <section className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold tracking-tight flex items-center gap-2">
                    <FolderTree className="h-5 w-5 text-indigo-600" />
                    Syllabus Taxonomy & Prerequisite Tree
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Active Blueprint: <span className="font-mono font-semibold text-foreground">{activeExamId}</span>
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveTab("catalog")}
                  className="text-xs"
                >
                  Change Exam Blueprint
                </Button>
              </div>

              <SyllabusTreeExplorer
                onStartTopicPractice={(topic) => {
                  openSocraticDrawer({ topicTitle: topic.title, topicId: topic.id });
                }}
              />
            </section>
          )}

          {/* TAB 3: Interactive Exam Player (Protected by RequireAuth) */}
          {activeTab === "solver" && (
            <section className="space-y-6">
              <RequireAuth
                allowedRoles={["student", "content_admin", "sys_admin"]}
                onPromptLogin={() => {
                  setAuthView("login");
                  setIsAuthModalOpen(true);
                }}
              >
                <ExamPlayer
                  onReturnToSyllabus={() => setActiveTab("syllabus")}
                  onOpenSocraticTutor={() => {
                    openSocraticDrawer({
                      topicTitle: "Cambridge Physics Mechanics",
                      questionStem: "Conservative potential energy force derivation",
                    });
                  }}
                />
              </RequireAuth>
            </section>
          )}

          {/* TAB 4: Analytics & Error Bank (Protected by RequireAuth) */}
          {activeTab === "analytics" && (
            <section className="space-y-6">
              <RequireAuth
                allowedRoles={["student", "content_admin", "sys_admin"]}
                onPromptLogin={() => {
                  setAuthView("login");
                  setIsAuthModalOpen(true);
                }}
              >
                <AnalyticsDashboard />
              </RequireAuth>
            </section>
          )}
        </main>

        {/* Global Socratic Tutor Floating Button & Slide-over Drawer */}
        <FloatingTutorButton />
        <SocraticTutorDrawer />
      </div>
    </TooltipProvider>
  );
}

export default App;
