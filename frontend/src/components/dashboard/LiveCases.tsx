import React from "react";
import CaseCard from "./CaseCard";
import { PatientCase } from "../../services/types";

interface LiveCasesProps {
  cases: PatientCase[];
  onCaseClick?: (caseId: string) => void;
}

const LiveCases: React.FC<LiveCasesProps> = ({ cases, onCaseClick }) => {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Live cases</h2>
        <div className="text-sm text-gray-400">
          {cases.length} active case{cases.length !== 1 ? "s" : ""}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cases.map((patientCase) => (
          <CaseCard
            key={patientCase.id}
            case={patientCase}
            onClick={onCaseClick}
          />
        ))}
      </div>

      {cases.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-2">No active cases</div>
          <div className="text-sm text-gray-500">
            All patients have been processed
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveCases;
