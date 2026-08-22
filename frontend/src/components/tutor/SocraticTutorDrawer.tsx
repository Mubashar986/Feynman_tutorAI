import * as React from "react";
import {
  Sparkles,
  Send,
  Lightbulb,
  HelpCircle,
  RotateCcw,
  BookOpen,
  GraduationCap,
  ShieldAlert,
} from "lucide-react";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
} from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { useSocraticTutorStore } from "@/stores/socraticTutorStore";
import { ChatMessageBubble } from "./ChatMessageBubble";
import type { PedagogicalMode } from "@/types/tutor";

export const SocraticTutorDrawer: React.FC = () => {
  const {
    isOpen,
    closeDrawer,
    activeContext,
    mode,
    setMode,
    messages,
    isStreaming,
    hintLevel,
    sendMessage,
    requestNextHint,
    clearHistory,
  } = useSocraticTutorStore();

  const [inputVal, setInputVal] = React.useState<string>("");
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputVal.trim() || isStreaming) return;
    const text = inputVal;
    setInputVal("");
    await sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const MODES: { id: PedagogicalMode; label: string; icon: React.ReactNode }[] = [
    { id: "socratic", label: "Socratic", icon: <Sparkles className="h-3 w-3" /> },
    { id: "hints", label: "3-Tier Hints", icon: <Lightbulb className="h-3 w-3" /> },
    { id: "teach_back", label: "Teach-Back", icon: <GraduationCap className="h-3 w-3" /> },
    { id: "adversarial", label: "Misconceptions", icon: <ShieldAlert className="h-3 w-3" /> },
  ];

  return (
    <Drawer open={isOpen} onOpenChange={(open) => !open && closeDrawer()}>
      <DrawerContent className="max-h-[92vh] flex flex-col">
        <div className="mx-auto flex h-full w-full max-w-2xl flex-col p-4 sm:p-6 overflow-hidden">
          {/* Header Area */}
          <DrawerHeader className="p-0 pb-3 border-b space-y-2 text-left">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-xs">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <DrawerTitle className="text-lg font-bold tracking-tight">
                    Socratic AI Tutor
                  </DrawerTitle>
                  <DrawerDescription className="text-xs">
                    Grounded interactive STEM guidance
                  </DrawerDescription>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearHistory}
                  className="h-8 text-xs text-muted-foreground hover:text-foreground gap-1"
                  title="Reset conversation"
                >
                  <RotateCcw className="h-3 w-3" /> Clear
                </Button>
              </div>
            </div>

            {/* Pedagogical Mode Switcher */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {MODES.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-all ${
                    mode === m.id
                      ? "bg-indigo-600 text-white shadow-xs"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  }`}
                >
                  {m.icon}
                  <span>{m.label}</span>
                </button>
              ))}
            </div>

            {/* Active Topic Context Pill */}
            {activeContext && (
              <div className="flex items-center gap-1.5 text-xs text-indigo-600 dark:text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-md border border-indigo-500/20 font-medium">
                <BookOpen className="h-3 w-3 shrink-0" />
                <span className="truncate">Context: {activeContext.topicTitle}</span>
              </div>
            )}
          </DrawerHeader>

          {/* Scrollable Message Stream */}
          <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1 min-h-[300px] max-h-[50vh]">
            {messages.map((msg, idx) => (
              <ChatMessageBubble
                key={msg.id}
                message={msg}
                isStreaming={isStreaming && idx === messages.length - 1}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Prompt Chips & Input Box */}
          <div className="border-t pt-3 space-y-3">
            {/* Quick Action Chips */}
            <div className="flex flex-wrap gap-2 text-xs">
              <button
                type="button"
                onClick={requestNextHint}
                disabled={isStreaming || hintLevel >= 3}
                className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] font-medium text-amber-700 dark:text-amber-300 hover:bg-amber-500/20 disabled:opacity-50"
              >
                <Lightbulb className="h-3 w-3" />
                {hintLevel === 0
                  ? "Get Hint #1"
                  : hintLevel < 3
                  ? `Get Hint #${hintLevel + 1}`
                  : "All 3 Hints Revealed"}
              </button>

              <button
                type="button"
                onClick={() => sendMessage("Why is this formula derived this way?")}
                disabled={isStreaming}
                className="inline-flex items-center gap-1 rounded-full border bg-muted/60 px-2.5 py-1 text-[11px] font-medium text-muted-foreground hover:bg-muted"
              >
                <HelpCircle className="h-3 w-3" /> "Why is this true?"
              </button>

              <button
                type="button"
                onClick={() => sendMessage("Can you give me an analogous physical example?")}
                disabled={isStreaming}
                className="inline-flex items-center gap-1 rounded-full border bg-muted/60 px-2.5 py-1 text-[11px] font-medium text-muted-foreground hover:bg-muted"
              >
                <Sparkles className="h-3 w-3" /> "Give me an analogy"
              </button>
            </div>

            {/* Message Input Form */}
            <form onSubmit={handleSend} className="relative flex items-center">
              <textarea
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question or explain your reasoning in your own words..."
                rows={1}
                disabled={isStreaming}
                className="w-full resize-none rounded-xl border border-input bg-background px-4 py-2.5 pr-12 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
              <Button
                type="submit"
                size="icon"
                variant="tutor"
                onClick={handleSend}
                disabled={!inputVal.trim() || isStreaming}
                className="absolute right-1.5 h-8 w-8 rounded-lg"
                aria-label="Send Message"
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </div>
      </DrawerContent>
    </Drawer>
  );
};
