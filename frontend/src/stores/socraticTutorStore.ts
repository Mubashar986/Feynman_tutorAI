import { create } from "zustand";
import type {
  SocraticTutorState,
  PedagogicalMode,
  TutorSessionContext,
  SocraticMessage,
  SourceCitation,
} from "@/types/tutor";
import { socraticClient, HINT_PROGRESSION } from "@/api/tutor";

const INITIAL_MESSAGE: SocraticMessage = {
  id: "msg_welcome",
  role: "tutor",
  text: "Hello! I am your **Socratic AI Tutor**. I won't just hand you the answer — I will ask guiding questions and point you to textbook principles so you master the concept yourself. How can I help you today?",
  timestamp: new Date().toISOString(),
};

export const useSocraticTutorStore = create<SocraticTutorState>((set, get) => ({
  isOpen: false,
  activeContext: null,
  mode: "socratic",
  messages: [INITIAL_MESSAGE],
  isStreaming: false,
  hintLevel: 0,

  openDrawer: (context?: TutorSessionContext) => {
    const updates: Partial<SocraticTutorState> = { isOpen: true };
    if (context) {
      updates.activeContext = context;
      updates.hintLevel = 0;
      // Add context welcome message if not already present
      const contextMsg: SocraticMessage = {
        id: `msg_ctx_${Date.now()}`,
        role: "system",
        text: `Active Topic Context: **${context.topicTitle}**`,
        timestamp: new Date().toISOString(),
      };
      updates.messages = [...get().messages, contextMsg];
    }
    set(updates);
  },

  closeDrawer: () => set({ isOpen: false }),

  setMode: (mode: PedagogicalMode) => set({ mode }),

  setContext: (context: TutorSessionContext) => set({ activeContext: context }),

  sendMessage: async (text: string) => {
    if (!text.trim() || get().isStreaming) return;

    const userMsg: SocraticMessage = {
      id: `msg_user_${Date.now()}`,
      role: "user",
      text: text.trim(),
      timestamp: new Date().toISOString(),
    };

    const tutorMsgId = `msg_tutor_${Date.now()}`;
    const initialTutorMsg: SocraticMessage = {
      id: tutorMsgId,
      role: "tutor",
      text: "",
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg, initialTutorMsg],
      isStreaming: true,
    }));

    try {
      const stream = socraticClient.streamResponse(
        text,
        get().activeContext,
        get().mode
      );

      let accumulatedText = "";
      let finalThoughts: string | undefined;
      let finalCitations: SourceCitation[] | undefined = undefined;

      for await (const chunkData of stream) {
        accumulatedText += chunkData.chunk;
        if (chunkData.thoughts) finalThoughts = chunkData.thoughts;
        if (chunkData.citations) finalCitations = chunkData.citations;

        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === tutorMsgId
              ? {
                  ...m,
                  text: accumulatedText,
                  thoughts: finalThoughts,
                  citations: finalCitations,
                }
              : m
          ),
        }));
      }
    } finally {
      set({ isStreaming: false });
    }
  },

  requestNextHint: async () => {
    if (get().isStreaming) return;

    const nextLevel = Math.min(3, get().hintLevel + 1);
    const hintData = HINT_PROGRESSION[nextLevel];
    if (!hintData) return;

    const userPrompt: SocraticMessage = {
      id: `msg_hint_req_${Date.now()}`,
      role: "user",
      text: `Give me Hint #${nextLevel}`,
      timestamp: new Date().toISOString(),
    };

    const tutorHintMsg: SocraticMessage = {
      id: `msg_hint_res_${Date.now()}`,
      role: "tutor",
      text: `**Hint Level ${nextLevel}/3:**\n\n${hintData.text}`,
      thoughts: hintData.thoughts,
      citations: hintData.citations,
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      hintLevel: nextLevel,
      messages: [...state.messages, userPrompt, tutorHintMsg],
    }));
  },

  clearHistory: () =>
    set({
      messages: [INITIAL_MESSAGE],
      hintLevel: 0,
      isStreaming: false,
    }),
}));
