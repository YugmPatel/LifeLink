import React from "react";
import { Clock, Heart, Activity, Droplets } from "lucide-react";
import {
  PatientCase,
  CASE_TYPE_COLORS,
  STATUS_COLORS,
} from "../../services/types";

interface CaseCardProps {
  case: PatientCase;
  onClick?: (caseId: string) => void;
}

const CaseCard: React.FC<CaseCardProps> = ({ case: patientCase, onClick }) => {
  const getStatusColor = (status: PatientCase["status"]) => {
    const colors = {
      Arriving: "bg-yellow-500",
      Triaged: "bg-blue-500",
      "In Treatment": "bg-green-500",
      Pending: "bg-orange-500",
      Admitted: "bg-green-600",
      Discharged: "bg-gray-500",
    };
    return colors[status] || "bg-gray-500";
  };

  const getTypeColor = (type: PatientCase["type"]) => {
    const colors = {
      STEMI: "text-red-500 border-red-500",
      Stroke: "text-orange-500 border-orange-500",
      Trauma: "text-red-600 border-red-600",
      General: "text-blue-500 border-blue-500",
      Pediatric: "text-purple-500 border-purple-500",
    };
    return colors[type] || "text-gray-500 border-gray-500";
  };

  const getPriorityIndicator = (priority: number) => {
    if (priority === 1) return "critical-pulse";
    if (priority === 2) return "animate-pulse-slow";
    return "";
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  return (
    <div
      className={`bg-gray-900 border border-gray-700 rounded-lg p-4 card-hover cursor-pointer ${getPriorityIndicator(
        patientCase.priority
      )}`}
      onClick={() => onClick?.(patientCase.id)}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="font-mono text-sm text-gray-300">
            {patientCase.id}
          </span>
          <span
            className={`px-2 py-1 text-xs font-medium border rounded ${getTypeColor(
              patientCase.type
            )}`}
          >
            {patientCase.type}
          </span>
        </div>
        <div className="flex items-center space-x-1 text-gray-400">
          <Clock className="w-4 h-4" />
          <span className="text-sm">
            {formatDuration(patientCase.duration)}
          </span>
        </div>
      </div>

      {/* Vitals */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="flex items-center space-x-2">
          <Heart className="w-4 h-4 text-red-500" />
          <span className="text-sm text-white">HR {patientCase.vitals.hr}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-blue-500" />
          <span className="text-sm text-white">
            BP {patientCase.vitals.bp_sys}/{patientCase.vitals.bp_dia}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <Droplets className="w-4 h-4 text-cyan-500" />
          <span className="text-sm text-white">
            SPO2 {patientCase.vitals.spo2}%
          </span>
        </div>
        <div className="text-sm text-gray-400">
          {patientCase.vitals.temp && `${patientCase.vitals.temp}°C`}
        </div>
      </div>

      {/* Status and Location */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div
            className={`w-2 h-2 rounded-full ${getStatusColor(
              patientCase.status
            )}`}
          ></div>
          <span className="text-sm text-gray-300">{patientCase.status}</span>
        </div>
        <span className="text-sm text-gray-400">{patientCase.location}</span>
      </div>

      {/* Lab ETA and Bed Assignment */}
      <div className="flex items-center justify-between text-xs text-gray-400">
        {patientCase.labETA && <span>Lab ETA {patientCase.labETA}m</span>}
        {patientCase.assignedBed && <span>{patientCase.assignedBed}</span>}
      </div>

      {/* Priority indicator for critical cases */}
      {patientCase.priority === 1 && (
        <div className="mt-2 text-xs text-red-400 font-medium">CRITICAL</div>
      )}
    </div>
  );
};

export default CaseCard;
