import * as React from "react";
import { ShieldAlert, LogIn } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import type { Role } from "@/types/auth";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export interface RequireAuthProps {
  children: React.ReactNode;
  allowedRoles?: Role[];
  onPromptLogin?: () => void;
  fallback?: React.ReactNode;
}

export const RequireAuth: React.FC<RequireAuthProps> = ({
  children,
  allowedRoles,
  onPromptLogin,
  fallback,
}) => {
  const { user, isAuthenticated } = useAuthStore();

  // 1. Unauthenticated Check
  if (!isAuthenticated || !user) {
    if (fallback) return <>{fallback}</>;

    return (
      <Card className="w-full max-w-lg mx-auto my-8 border-indigo-500/30 bg-card shadow-md">
        <CardHeader>
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
            <LogIn className="h-5 w-5" />
            <CardTitle className="text-lg">Authentication Required</CardTitle>
          </div>
          <CardDescription>
            You must be signed in to access this adaptive learning resource.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Please log in to track your mastery scores, save misconception diagnostics, and interact with the Socratic AI Tutor.
          </p>
        </CardContent>
        {onPromptLogin && (
          <CardFooter>
            <Button variant="tutor" onClick={onPromptLogin} className="w-full">
              Sign In to Continue
            </Button>
          </CardFooter>
        )}
      </Card>
    );
  }

  // 2. Role-Based Authorization Check
  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    if (fallback) return <>{fallback}</>;

    return (
      <Card className="w-full max-w-lg mx-auto my-8 border-rose-500/40 bg-card shadow-md">
        <CardHeader>
          <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400">
            <ShieldAlert className="h-5 w-5" />
            <CardTitle className="text-lg">Access Denied (403)</CardTitle>
          </div>
          <CardDescription>
            Your account does not have permission to view this section.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            Current Role: <Badge variant="outline" className="font-semibold capitalize">{user.role}</Badge>
          </p>
          <p>
            Required Role: <Badge variant="secondary" className="capitalize">{allowedRoles.join(" or ")}</Badge>
          </p>
        </CardContent>
      </Card>
    );
  }

  return <>{children}</>;
};
