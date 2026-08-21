import * as React from "react";
import {
  GraduationCap,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Moon,
  Sun,
  Layers,
  BookOpen,
  ArrowRight,
  LogIn,
  ShieldAlert,
  UserCheck,
  FolderTree,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Drawer, DrawerTrigger, DrawerContent, DrawerHeader, DrawerTitle, DrawerDescription, DrawerFooter, DrawerClose } from "@/components/ui/drawer";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import { LaTeXRenderer } from "@/components/common/LaTeXRenderer";
import { useAuthStore } from "@/stores/authStore";
import { LoginForm } from "@/components/auth/LoginForm";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { UserProfileMenu } from "@/components/auth/UserProfileMenu";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { ExamCatalogGrid } from "@/components/curriculum/ExamCatalogGrid";
import { SyllabusTreeExplorer } from "@/components/curriculum/SyllabusTreeExplorer";
import { useCurriculumStore } from "@/stores/curriculumStore";

export function App() {
  const [isDark, setIsDark] = React.useState<boolean>(false);
  const [selectedOption, setSelectedOption] = React.useState<string | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = React.useState<boolean>(false);
  const [authView, setAuthView] = React.useState<"login" | "register">("login");
  const [activeTab, setActiveTab] = React.useState<"catalog" | "syllabus" | "solver">("syllabus");

  const { user, isAuthenticated } = useAuthStore();
  const { activeExamId } = useCurriculumStore();

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
                <Sparkles className="h-3.5 w-3.5 text-indigo-500" /> Diagnostic Solver
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
        <div className="flex md:hidden border-b bg-muted/20 px-4 py-2 justify-center gap-2 text-xs">
          <button
            onClick={() => setActiveTab("catalog")}
            className={`px-3 py-1 rounded-md ${activeTab === "catalog" ? "bg-card font-bold shadow-sm" : "text-muted-foreground"}`}
          >
            Catalog
          </button>
          <button
            onClick={() => setActiveTab("syllabus")}
            className={`px-3 py-1 rounded-md ${activeTab === "syllabus" ? "bg-card font-bold shadow-sm" : "text-muted-foreground"}`}
          >
            Syllabus Tree
          </button>
          <button
            onClick={() => setActiveTab("solver")}
            className={`px-3 py-1 rounded-md ${activeTab === "solver" ? "bg-card font-bold shadow-sm" : "text-muted-foreground"}`}
          >
            Diagnostic Solver
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
                "Task 2.3: Exam Blueprint Catalog & Syllabus Tree"
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
              Explore official examination blueprints, inspect formulas with LaTeX KaTeX rendering, and follow prerequisite paths.
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
                onStartTopicPractice={() => setActiveTab("solver")}
              />
            </section>
          )}

          {/* TAB 3: Diagnostic Solver & Component Showcase */}
          {activeTab === "solver" && (
            <section className="space-y-8">
              {/* Pedagogical Tokens & Primitive Gallery */}
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <Card className="flex flex-col justify-between">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                      Pedagogical Mastery Tokens
                    </CardTitle>
                    <CardDescription>Semantic badges for cognitive state tracking.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="masteryHigh" className="gap-1">
                        <CheckCircle2 className="h-3 w-3" /> Mastered (92%)
                      </Badge>
                      <Badge variant="masteryMedium" className="gap-1">
                        <AlertTriangle className="h-3 w-3" /> Developing (68%)
                      </Badge>
                      <Badge variant="masteryLow" className="gap-1">
                        <XCircle className="h-3 w-3" /> Misconception (34%)
                      </Badge>
                      <Badge variant="socratic" className="gap-1">
                        <Sparkles className="h-3 w-3" /> Socratic Tutor Active
                      </Badge>
                    </div>
                  </CardContent>
                  <CardFooter className="text-xs text-muted-foreground">
                    Tokens defined in DESIGN_SYSTEM_TYPOGRAPHY.md
                  </CardFooter>
                </Card>

                <Card className="flex flex-col justify-between">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Layers className="h-5 w-5 text-indigo-500" />
                      Button Primitives
                    </CardTitle>
                    <CardDescription>CVA accessible button variants.</CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-wrap gap-2">
                    <Button variant="default" size="sm">Primary</Button>
                    <Button variant="mastery" size="sm">Mastery</Button>
                    <Button variant="tutor" size="sm">Socratic</Button>
                    <Button variant="secondary" size="sm">Secondary</Button>
                    <Button variant="outline" size="sm">Outline</Button>
                    <Button variant="destructive" size="sm">Destructive</Button>
                  </CardContent>
                  <CardFooter className="text-xs text-muted-foreground">
                    Radix Slot + focus-visible ring states
                  </CardFooter>
                </Card>

                <Card className="flex flex-col justify-between">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <BookOpen className="h-5 w-5 text-amber-500" />
                      Socratic Drawer
                    </CardTitle>
                    <CardDescription>Slide-over drawer powered by Vaul.</CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-wrap gap-2">
                    <Drawer>
                      <DrawerTrigger asChild>
                        <Button variant="tutor" size="sm" className="gap-1">
                          <Sparkles className="h-3.5 w-3.5" /> Open Socratic Drawer
                        </Button>
                      </DrawerTrigger>
                      <DrawerContent>
                        <div className="mx-auto w-full max-w-xl p-6 space-y-4">
                          <DrawerHeader className="p-0">
                            <DrawerTitle className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
                              <Sparkles className="h-5 w-5" /> Socratic AI Tutor
                            </DrawerTitle>
                            <DrawerDescription>
                              Let's break down why acceleration remains constant in free fall.
                            </DrawerDescription>
                          </DrawerHeader>
                          <div className="rounded-lg border bg-muted/40 p-4 space-y-2 text-sm">
                            <p className="font-semibold text-foreground">Tutor Question:</p>
                            <p className="italic text-muted-foreground">
                              "If gravitational force is proportional to mass \( F_g = mg \), why do heavy and light objects accelerate at the exact same rate?"
                            </p>
                            <div className="mt-2 pt-2 border-t text-xs text-indigo-600 dark:text-indigo-400">
                              Hint: Think about Newton's Second Law \( F = ma \).
                            </div>
                          </div>
                          <DrawerFooter className="p-0 pt-4">
                            <DrawerClose asChild>
                              <Button variant="outline">Close Drawer</Button>
                            </DrawerClose>
                          </DrawerFooter>
                        </div>
                      </DrawerContent>
                    </Drawer>
                  </CardContent>
                  <CardFooter className="text-xs text-muted-foreground">
                    Fully keyboard accessible with focus trap
                  </CardFooter>
                </Card>
              </div>

              {/* Protected Diagnostic Problem Solver */}
              <div className="rounded-xl border bg-card p-6 shadow-sm space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
                  <div>
                    <h3 className="text-xl font-bold tracking-tight flex items-center gap-2">
                      <Sparkles className="h-5 w-5 text-indigo-600" />
                      Protected Diagnostic Problem Solver (KaTeX STEM)
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Adaptive problem solver protected by client-side Route Guard.
                    </p>
                  </div>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <HelpCircle className="h-5 w-5 text-muted-foreground" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      Rendered via KaTeX synchronous string-to-HTML parser
                    </TooltipContent>
                  </Tooltip>
                </div>

                <RequireAuth
                  allowedRoles={["student", "content_admin", "sys_admin"]}
                  onPromptLogin={() => {
                    setAuthView("login");
                    setIsAuthModalOpen(true);
                  }}
                >
                  <div className="space-y-4">
                    <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                          Sample Question #14 — AP Physics / Calculus Mechanics
                        </span>
                        <Badge variant="masteryMedium">Difficulty: 0.74 IRT</Badge>
                      </div>

                      <p className="text-base leading-relaxed">
                        A particle of mass <LaTeXRenderer formula="m" /> moves along the x-axis subject to a restorative force. 
                        The potential energy function is given by:
                      </p>

                      <LaTeXRenderer
                        formula="U(x) = \frac{1}{2} k x^2 + \alpha x^4"
                        displayMode={true}
                        className="text-lg text-indigo-600 dark:text-indigo-400"
                      />

                      <p className="text-base leading-relaxed">
                        Which of the following expressions represents the particle's acceleration <LaTeXRenderer formula="a(x)" /> at position <LaTeXRenderer formula="x" />?
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      {[
                        { id: "A", formula: "a(x) = -\\frac{k}{m}x - \\frac{4\\alpha}{m}x^3", label: "Option A" },
                        { id: "B", formula: "a(x) = -kx - \\alpha x^3", label: "Option B" },
                        { id: "C", formula: "a(x) = \\frac{k}{m}x + \\frac{2\\alpha}{m}x^3", label: "Option C" },
                        { id: "D", formula: "a(x) = -\\frac{k}{m}x + \\frac{4\\alpha}{m}x^3", label: "Option D" },
                      ].map((opt) => (
                        <button
                          key={opt.id}
                          aria-label={opt.label}
                          onClick={() => setSelectedOption(opt.id)}
                          className={`flex items-center justify-between rounded-lg border p-4 text-left transition-all ${
                            selectedOption === opt.id
                              ? "border-indigo-600 bg-indigo-500/10 ring-2 ring-indigo-600"
                              : "hover:border-border/80 hover:bg-muted/50"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <span className="flex h-7 w-7 items-center justify-center rounded-md border text-xs font-bold">
                              {opt.id}
                            </span>
                            <LaTeXRenderer formula={opt.formula} />
                          </div>
                          {selectedOption === opt.id && (
                            <CheckCircle2 className="h-5 w-5 text-indigo-600" />
                          )}
                        </button>
                      ))}
                    </div>

                    {selectedOption && (
                      <div className="flex items-center justify-between pt-2">
                        <p className="text-sm text-muted-foreground">
                          Selected: <strong>Option {selectedOption}</strong>
                        </p>
                        <Button variant="tutor" size="sm" className="gap-2">
                          Submit Answer <ArrowRight className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                </RequireAuth>
              </div>

              {/* RBAC Guard Area */}
              <section className="rounded-xl border border-dashed border-border p-6 bg-muted/10 space-y-3">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <ShieldAlert className="h-4 w-4 text-amber-500" />
                  Role-Based Access Control (RBAC) Verification Area
                </div>
                <p className="text-xs text-muted-foreground">
                  Demonstrates how <code>&lt;RequireAuth allowedRoles={["content_admin", "sys_admin"]} /&gt;</code> denies access if a logged-in user only possesses the <code>student</code> role.
                </p>
                <RequireAuth
                  allowedRoles={["content_admin", "sys_admin"]}
                  fallback={
                    <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-300">
                      🔒 Admin-only blueprint management tools are hidden for standard student accounts.
                    </div>
                  }
                >
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-md text-xs text-emerald-600">
                    ✅ Content Administrator clearance granted. You have access to syllabus upload & question bank approval tools.
                  </div>
                </RequireAuth>
              </section>
            </section>
          )}
        </main>
      </div>
    </TooltipProvider>
  );
}

export default App;
