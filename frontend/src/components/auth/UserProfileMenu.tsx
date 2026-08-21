import * as React from "react";
import { LogOut, User as UserIcon, BookOpen, Shield } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export const UserProfileMenu: React.FC = () => {
  const { user, logout } = useAuthStore();
  const [isOpen, setIsOpen] = React.useState<boolean>(false);
  const menuRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user) return null;

  const initials = user.fullName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="User Profile Menu"
        aria-expanded={isOpen}
        className="flex items-center gap-2 rounded-full border border-border/80 bg-card p-1 pr-3 transition-all hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white shadow-sm">
          {initials}
        </div>
        <div className="hidden sm:flex flex-col text-left">
          <span className="text-xs font-semibold leading-tight text-foreground">
            {user.fullName}
          </span>
          <span className="text-[10px] text-muted-foreground capitalize">
            {user.role.replace("_", " ")}
          </span>
        </div>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 rounded-lg border bg-popover p-4 shadow-xl z-50 text-popover-foreground animate-in fade-in-0 zoom-in-95">
          <div className="space-y-2 border-b pb-3">
            <div className="flex items-center gap-2">
              <UserIcon className="h-4 w-4 text-indigo-600" />
              <p className="text-sm font-semibold truncate">{user.fullName}</p>
            </div>
            <p className="text-xs text-muted-foreground truncate">{user.email}</p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              <Badge variant="socratic" className="text-[10px] py-0 px-2 capitalize">
                <Shield className="h-2.5 w-2.5 mr-1" />
                {user.role.replace("_", " ")}
              </Badge>
              {user.targetExam && (
                <Badge variant="outline" className="text-[10px] py-0 px-2">
                  <BookOpen className="h-2.5 w-2.5 mr-1" />
                  {user.targetExam}
                </Badge>
              )}
            </div>
          </div>

          <div className="pt-3">
            <Button
              variant="destructive"
              size="sm"
              className="w-full justify-start text-xs gap-2"
              onClick={() => {
                setIsOpen(false);
                logout();
              }}
            >
              <LogOut className="h-3.5 w-3.5" />
              Sign Out
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
