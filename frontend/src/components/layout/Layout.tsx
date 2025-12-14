import React, { useState, useEffect } from "react";
import Header from "./Header";
import MetricsCards from "../dashboard/MetricsCards";
import LiveCases from "../dashboard/LiveCases";
import ActivityLog from "../dashboard/ActivityLog";
import ChatInterface from "../chat/ChatInterface";
import { useRealTimeDashboard, useRealTimeChat } from "../../hooks/useSocket";
import { api } from "../../services/api";
import { mockData, simulatePatientArrival } from "../../services/mockData";
import {
  PatientCase,
  DashboardMetrics,
  ActivityEntry,
  ChatMessage,
} from "../../services/types";

const Layout: React.FC = () => {
  // Use real-time hooks for WebSocket communication
  const {
    metrics: realTimeMetrics,
    cases: realTimeCases,
    activities: realTimeActivities,
    isConnected: dashboardConnected,
    setMetrics,
    setCases,
    setActivities,
  } = useRealTimeDashboard();

  const {
    messages,
    sendMessage: sendChatMessage,
    isConnected: chatConnected,
  } = useRealTimeChat();

  // Local state with fallbacks
  const [localMetrics, setLocalMetrics] = useState<DashboardMetrics>(
    mockData.metrics
  );
  const [localCases, setLocalCases] = useState<PatientCase[]>(mockData.cases);
  const [localActivities, setLocalActivities] = useState<ActivityEntry[]>(
    mockData.activities
  );

  // Use real-time data if available, otherwise use local/mock data
  const metrics = realTimeMetrics || localMetrics;
  const cases = realTimeCases.length > 0 ? realTimeCases : localCases;
  const activities =
    realTimeActivities.length > 0 ? realTimeActivities : localActivities;
  const isConnected = dashboardConnected || chatConnected;

  // Initialize with mock data and simulate updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Update metrics timestamp
      setLocalMetrics((prev) => ({
        ...prev,
        last_updated: new Date(),
      }));

      // Simulate occasional new activities if no real-time data
      if (realTimeActivities.length === 0 && Math.random() < 0.3) {
        const newActivity: ActivityEntry = {
          id: String(Date.now()),
          timestamp: new Date(),
          type: ["Lab", "Pharm", "System"][
            Math.floor(Math.random() * 3)
          ] as ActivityEntry["type"],
          message: [
            "Lab results ready",
            "Medication prepared",
            "Bed assignment updated",
            "Doctor notification sent",
          ][Math.floor(Math.random() * 4)],
          status: ["Ready", "Complete", "Pending"][
            Math.floor(Math.random() * 3)
          ] as ActivityEntry["status"],
        };

        setLocalActivities((prev) => [newActivity, ...prev].slice(0, 20));
      }
    }, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, [realTimeActivities.length]);

  const handleSimulateSTEMI = async () => {
    try {
      console.log("Triggering STEMI simulation...");
      const response = await api.simulateSTEMI();
      console.log("STEMI simulation response:", response);

      // The real-time hooks will automatically update the UI via WebSocket
      // If WebSocket is not connected, update local state as fallback
      if (!isConnected) {
        const newPatient = simulatePatientArrival("STEMI");
        setLocalCases((prev) => [newPatient, ...prev]);
        setLocalMetrics((prev) => ({
          ...prev,
          active_cases: prev.active_cases + 1,
          last_updated: new Date(),
        }));
      }
    } catch (error) {
      console.error("Error triggering STEMI simulation:", error);

      // Fallback to local simulation
      const newPatient = simulatePatientArrival("STEMI");
      setLocalCases((prev) => [newPatient, ...prev]);
      setLocalMetrics((prev) => ({
        ...prev,
        active_cases: prev.active_cases + 1,
        lastUpdated: new Date(),
      }));
    }
  };

  const handleSimulateStroke = async () => {
    try {
      console.log("Triggering Stroke simulation...");
      const response = await api.simulateStroke();
      console.log("Stroke simulation response:", response);

      // The real-time hooks will automatically update the UI via WebSocket
      if (!isConnected) {
        const newPatient = simulatePatientArrival("Stroke");
        setLocalCases((prev) => [newPatient, ...prev]);
        setLocalMetrics((prev) => ({
          ...prev,
          active_cases: prev.active_cases + 1,
          last_updated: new Date(),
        }));
      }
    } catch (error) {
      console.error("Error triggering Stroke simulation:", error);

      // Fallback to local simulation
      const newPatient = simulatePatientArrival("Stroke");
      setLocalCases((prev) => [newPatient, ...prev]);
      setLocalMetrics((prev) => ({
        ...prev,
        active_cases: prev.active_cases + 1,
        last_updated: new Date(),
      }));
    }
  };

  const handleSendMessage = (message: string) => {
    console.log("Sending message:", message);

    try {
      // Use the real-time chat hook which handles WebSocket communication
      sendChatMessage(message);
    } catch (error) {
      console.error("Error sending message via WebSocket:", error);

      // Fallback: Add message locally and simulate response
      const userMessage: ChatMessage = {
        id: `user_${Date.now()}`,
        content: message,
        timestamp: new Date(),
        sender: "User",
        type: "user",
      };

      // Since we can't directly update the real-time chat messages,
      // we'll log this for debugging
      console.log("Message sent (fallback mode):", userMessage);
    }
  };

  const handleCaseClick = (caseId: string) => {
    console.log("Case clicked:", caseId);
    // Here you would typically open a detailed view or modal
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <Header
        onSimulateSTEMI={handleSimulateSTEMI}
        onSimulateStroke={handleSimulateStroke}
        isConnected={isConnected}
      />

      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-8">
            {/* Metrics Cards */}
            <MetricsCards metrics={metrics} />

            {/* Live Cases */}
            <LiveCases cases={cases} onCaseClick={handleCaseClick} />

            {/* Activity Log */}
            <ActivityLog entries={activities} />
          </div>

          {/* Chat Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <ChatInterface
                messages={messages.length > 0 ? messages : mockData.messages}
                onSendMessage={handleSendMessage}
                isConnected={isConnected}
                className="h-[600px]"
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
