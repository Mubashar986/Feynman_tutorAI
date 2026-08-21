import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { AuthState, User } from "@/types/auth";

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setAuth: (user: User, token: string) =>
        set({
          user,
          token,
          isAuthenticated: true,
          error: null,
          isLoading: false,
        }),

      logout: () =>
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
          isLoading: false,
        }),

      updateUser: (updates: Partial<User>) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      setError: (error: string | null) => set({ error, isLoading: false }),

      setLoading: (isLoading: boolean) => set({ isLoading }),
    }),
    {
      name: "feynman_auth_state",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
