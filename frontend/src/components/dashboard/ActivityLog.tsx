import React, { useState } from "react";
import { Clock, CheckCircle, AlertCircle, XCircle } from "lucide-react";
import { ActivityEntry } from "../../services/types";

interface ActivityLogProps {
  entries: ActivityEntry[];
  maxEntries?: number;
}

const ActivityLog: React.FC<ActivityLogProps> = ({
  entries,
  maxEntries = 10,
}) => {
  const [activeTab, setActiveTab] = useState<
    "all" | "Lab" | "Pharm" | "Activity"
  >("all");

  const tabs = [
    { id: "all" as const, label: "Activity", count: entries.length },
    {
      id: "Lab" as const,
      label: "Lab",
      count: entries.filter((e) => e.type === "Lab").length,
    },
    {
      id: "Pharm" as const,
      label: "Pharm",
      count: entries.filter((e) => e.type === "Pharm").length,
    },
  ];

  const filteredEntries =
    activeTab === "all"
      ? entries
      : entries.filter((entry) => entry.type === activeTab);

  const displayEntries = filteredEntries.slice(0, maxEntries);

  const getStatusIcon = (status: ActivityEntry["status"]) => {
    switch (status) {
      case "Complete":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "Ready":
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case "Pending":
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case "In Progress":
        return <AlertCircle className="w-4 h-4 text-blue-500" />;
      case "Failed":
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: ActivityEntry["status"]) => {
    switch (status) {
      case "Complete":
        return "text-green-400";
      case "Ready":
        return "text-blue-400";
      case "Pending":
        return "text-yellow-400";
      case "In Progress":
        return "text-blue-400";
      case "Failed":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  const formatRelativeTime = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    return `${diffHours}h ago`;
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg">
      {/* Tab Navigation */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-8 px-6 py-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "text-blue-400 border-b-2 border-blue-400 pb-2"
                  : "text-gray-400 hover:text-gray-300"
              }`}
            >
              <span>{tab.label}</span>
              {tab.count > 0 && (
                <span className="bg-gray-700 text-xs px-2 py-1 rounded-full">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Activity List */}
      <div className="p-6">
        <div className="space-y-4">
          {displayEntries.map((entry) => (
            <div key={entry.id} className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-1">
                {getStatusIcon(entry.status)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-white">
                      {entry.message}
                    </span>
                    <span
                      className={`text-xs px-2 py-1 rounded ${getStatusColor(
                        entry.status
                      )}`}
                    >
                      {entry.status}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-400">
                    <span>{formatRelativeTime(entry.timestamp)}</span>
                    <span>{formatTime(entry.timestamp)}</span>
                  </div>
                </div>

                {entry.caseId && (
                  <div className="mt-1 text-xs text-gray-500">
                    Case: {entry.caseId}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {displayEntries.length === 0 && (
          <div className="text-center py-8">
            <div className="text-gray-400 mb-2">No activity</div>
            <div className="text-sm text-gray-500">
              {activeTab === "all"
                ? "No recent activity"
                : `No ${activeTab.toLowerCase()} activity`}
            </div>
          </div>
        )}

        {filteredEntries.length > maxEntries && (
          <div className="mt-4 text-center">
            <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
              View all {filteredEntries.length} entries
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityLog;
