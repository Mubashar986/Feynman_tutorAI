import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { SimulationState, ExamBlueprint, SimulationMode, CalibratedScoreReport } from "@/types/simulation";
import { EXAM_BLUEPRINTS, SAMPLE_PHYSICS_SCORE_REPORT } from "@/api/simulation";

export const useExamSimulationStore = create<SimulationState>()(
  persist(
    (set) => ({
      activeBlueprint: EXAM_BLUEPRINTS[0],
      simulationMode: "proctored",
      activeScoreReport: null,
      simulationHistory: [SAMPLE_PHYSICS_SCORE_REPORT],

      setBlueprint: (blueprint: ExamBlueprint) =>
        set({ activeBlueprint: blueprint, activeScoreReport: null }),

      setSimulationMode: (mode: SimulationMode) =>
        set({ simulationMode: mode }),

      setScoreReport: (report: CalibratedScoreReport | null) =>
        set((state) => ({
          activeScoreReport: report,
          simulationHistory: report
            ? [report, ...state.simulationHistory.filter((r) => r.id !== report.id)]
            : state.simulationHistory,
        })),

      resetSimulation: () =>
        set({
          activeBlueprint: EXAM_BLUEPRINTS[0],
          simulationMode: "proctored",
          activeScoreReport: null,
        }),
    }),
    {
      name: "feynman_exam_simulation_state",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        activeBlueprint: state.activeBlueprint,
        simulationMode: state.simulationMode,
        simulationHistory: state.simulationHistory,
      }),
    }
  )
);
