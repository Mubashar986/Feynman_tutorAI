import * as React from "react";
import { useExamSimulationStore } from "@/stores/examSimulationStore";
import { ExamSimulationLauncher } from "./ExamSimulationLauncher";
import { SimulationScoreReport } from "./SimulationScoreReport";

export interface ExamSimulationViewProps {
  onStartExamSession: () => void;
}

export const ExamSimulationView: React.FC<ExamSimulationViewProps> = ({
  onStartExamSession,
}) => {
  const { activeScoreReport, setScoreReport } = useExamSimulationStore();

  if (activeScoreReport) {
    return (
      <SimulationScoreReport
        report={activeScoreReport}
        onRetake={() => {
          setScoreReport(null);
          onStartExamSession();
        }}
        onBackToLauncher={() => setScoreReport(null)}
      />
    );
  }

  return (
    <ExamSimulationLauncher
      onStartSimulation={() => {
        onStartExamSession();
      }}
    />
  );
};
