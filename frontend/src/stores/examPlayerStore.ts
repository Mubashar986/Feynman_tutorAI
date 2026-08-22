import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ExamPlayerState, ExamSession } from "@/types/exam";
import { SAMPLE_PHYSICS_EXAM, examClient } from "@/api/exam";

export const useExamPlayerStore = create<ExamPlayerState>()(
  persist(
    (set, get) => ({
      session: SAMPLE_PHYSICS_EXAM,
      currentQuestionIndex: 0,
      answers: {},
      flaggedQuestionIds: [],
      timeRemainingSeconds: SAMPLE_PHYSICS_EXAM.durationMinutes * 60,
      isSubmitted: false,
      isReviewModalOpen: false,
      scoreSummary: null,

      startSession: (session: ExamSession) =>
        set({
          session,
          currentQuestionIndex: 0,
          answers: {},
          flaggedQuestionIds: [],
          timeRemainingSeconds: session.durationMinutes * 60,
          isSubmitted: false,
          isReviewModalOpen: false,
          scoreSummary: null,
        }),

      selectAnswer: (questionId: string, optionId: string) =>
        set((state) => {
          if (state.isSubmitted) return state;
          return {
            answers: {
              ...state.answers,
              [questionId]: optionId,
            },
          };
        }),

      clearAnswer: (questionId: string) =>
        set((state) => {
          if (state.isSubmitted) return state;
          const updated = { ...state.answers };
          delete updated[questionId];
          return { answers: updated };
        }),

      toggleFlag: (questionId: string) =>
        set((state) => {
          const isFlagged = state.flaggedQuestionIds.includes(questionId);
          return {
            flaggedQuestionIds: isFlagged
              ? state.flaggedQuestionIds.filter((id) => id !== questionId)
              : [...state.flaggedQuestionIds, questionId],
          };
        }),

      nextQuestion: () =>
        set((state) => {
          if (!state.session) return state;
          const nextIndex = Math.min(
            state.session.questions.length - 1,
            state.currentQuestionIndex + 1
          );
          return { currentQuestionIndex: nextIndex };
        }),

      prevQuestion: () =>
        set((state) => {
          const prevIndex = Math.max(0, state.currentQuestionIndex - 1);
          return { currentQuestionIndex: prevIndex };
        }),

      goToQuestion: (index: number) =>
        set((state) => {
          if (!state.session) return state;
          if (index >= 0 && index < state.session.questions.length) {
            return { currentQuestionIndex: index };
          }
          return state;
        }),

      setIsReviewModalOpen: (isOpen: boolean) => set({ isReviewModalOpen: isOpen }),

      submitExam: () => {
        const state = get();
        if (!state.session || state.isSubmitted) return;

        const timeSpent =
          state.session.durationMinutes * 60 - state.timeRemainingSeconds;
        const summary = examClient.gradeExamSession(
          state.session,
          state.answers,
          timeSpent
        );

        set({
          isSubmitted: true,
          isReviewModalOpen: false,
          scoreSummary: summary,
        });
      },

      resetSession: () => {
        const defaultSession = SAMPLE_PHYSICS_EXAM;
        set({
          session: defaultSession,
          currentQuestionIndex: 0,
          answers: {},
          flaggedQuestionIds: [],
          timeRemainingSeconds: defaultSession.durationMinutes * 60,
          isSubmitted: false,
          isReviewModalOpen: false,
          scoreSummary: null,
        });
      },

      tickTimer: () =>
        set((state) => {
          if (state.isSubmitted || state.timeRemainingSeconds <= 0) {
            if (!state.isSubmitted && state.session) {
              const summary = examClient.gradeExamSession(
                state.session,
                state.answers,
                state.session.durationMinutes * 60
              );
              return {
                timeRemainingSeconds: 0,
                isSubmitted: true,
                scoreSummary: summary,
              };
            }
            return { timeRemainingSeconds: 0 };
          }
          return { timeRemainingSeconds: state.timeRemainingSeconds - 1 };
        }),
    }),
    {
      name: "feynman_active_exam_state",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        session: state.session,
        currentQuestionIndex: state.currentQuestionIndex,
        answers: state.answers,
        flaggedQuestionIds: state.flaggedQuestionIds,
        timeRemainingSeconds: state.timeRemainingSeconds,
        isSubmitted: state.isSubmitted,
        scoreSummary: state.scoreSummary,
      }),
    }
  )
);
