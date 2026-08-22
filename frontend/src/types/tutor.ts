/**
 * TypeScript types for the Socratic AI Tutor & Streaming Dialogue Engine.
 */

export type PedagogicalMode = "socratic" | "hints" | "teach_back" | "adversarial";

export interface SourceCitation {
  id: string;
  title: string;
  syllabusCode: string; // e.g. "Cambridge 9702 §4.2"
  pageNumber?: number;
  snippet: string;
}

export interface SocraticMessage {
  id: string;
  role: "user" | "tutor" | "system";
  text: string;
  thoughts?: string; // AI reasoning trace
  citations?: SourceCitation[];
  timestamp: string;
}

export interface TutorSessionContext {
  topicId?: string;
  topicTitle: string;
  questionStem?: string;
  studentAnswer?: string;
}

export interface SocraticTutorState {
  isOpen: boolean;
  activeContext: TutorSessionContext | null;
  mode: PedagogicalMode;
  messages: SocraticMessage[];
  isStreaming: boolean;
  hintLevel: number; // 1 to 3

  // Actions
  openDrawer: (context?: TutorSessionContext) => void;
  closeDrawer: () => void;
  setMode: (mode: PedagogicalMode) => void;
  setContext: (context: TutorSessionContext) => void;
  sendMessage: (text: string) => Promise<void>;
  requestNextHint: () => Promise<void>;
  clearHistory: () => void;
}
