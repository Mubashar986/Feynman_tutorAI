import * as React from "react";
import { LogIn, AlertCircle, Sparkles, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";
import { authClient, DEMO_USERS } from "@/api/auth";

export interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({
  onSuccess,
  onSwitchToRegister,
}) => {
  const [email, setEmail] = React.useState<string>("");
  const [password, setPassword] = React.useState<string>("");
  const [formError, setFormError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState<boolean>(false);

  const setAuth = useAuthStore((state) => state.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!email.trim()) {
      setFormError("Please enter your email address.");
      return;
    }
    if (!password) {
      setFormError("Please enter your password.");
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await authClient.login({ email: email.trim(), password });
      setAuth(res.user, res.token);
      if (onSuccess) onSuccess();
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to log in. Please check your credentials.";
      setFormError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemoAccount = (demoEmail: string) => {
    const demo = DEMO_USERS[demoEmail];
    if (demo) {
      setEmail(demo.user.email);
      setPassword(demo.password);
      setFormError(null);
    }
  };

  return (
    <Card className="w-full max-w-md shadow-lg border-border/80">
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl font-bold tracking-tight">Sign In</CardTitle>
          <div className="h-8 w-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
            <LogIn className="h-4 w-4" />
          </div>
        </div>
        <CardDescription>
          Enter your credentials to access your adaptive study session.
        </CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {formError && (
            <div
              role="alert"
              className="flex items-center gap-2 rounded-md border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-600 dark:text-rose-400 font-medium"
            >
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="login-email">Email Address</Label>
            <Input
              id="login-email"
              type="email"
              placeholder="student@feynman.ai"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
              autoComplete="email"
              required
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="login-password">Password</Label>
            </div>
            <Input
              id="login-password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isSubmitting}
              autoComplete="current-password"
              required
            />
          </div>

          {/* 1-Click Quick Demo Accounts */}
          <div className="pt-2 border-t space-y-2">
            <span className="text-xs text-muted-foreground font-medium block">
              Quick-Fill Demo Accounts:
            </span>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="flex-1 text-xs gap-1.5"
                onClick={() => fillDemoAccount("student@feynman.ai")}
              >
                <Sparkles className="h-3 w-3 text-emerald-500" /> Student Demo
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="flex-1 text-xs gap-1.5"
                onClick={() => fillDemoAccount("admin@feynman.ai")}
              >
                <ShieldCheck className="h-3 w-3 text-indigo-500" /> Admin Demo
              </Button>
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col space-y-3">
          <Button
            type="submit"
            variant="tutor"
            className="w-full"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Signing In..." : "Sign In to Feynman"}
          </Button>

          {onSwitchToRegister && (
            <p className="text-xs text-center text-muted-foreground">
              Don't have an account?{" "}
              <button
                type="button"
                onClick={onSwitchToRegister}
                className="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline"
              >
                Create Account
              </button>
            </p>
          )}
        </CardFooter>
      </form>
    </Card>
  );
};
