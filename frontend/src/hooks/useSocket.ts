/**
 * React Hook for Socket.IO Integration
 * Provides real-time WebSocket functionality to React components
 */

import { useEffect, useState, useCallback, useRef } from "react";
import { socketService, SocketEventHandlers } from "../services/socket";
import {
  PatientCase,
  ChatMessage,
  DashboardMetrics,
  ActivityEntry,
} from "../services/types";

export interface UseSocketReturn {
  isConnected: boolean;
  connectionId: string | undefined;
  sendMessage: (message: string, sender?: string) => void;
  requestDashboardUpdate: () => void;
  joinRoom: (room: string) => void;
  leaveRoom: (room: string) => void;
  ping: () => Promise<number>;
  reconnect: () => void;
  lastError: string | null;
}

export const useSocket = (handlers?: SocketEventHandlers): UseSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionId, setConnectionId] = useState<string | undefined>();
  const [lastError, setLastError] = useState<string | null>(null);
  const handlersRef = useRef(handlers);

  // Update handlers ref when handlers change
  useEffect(() => {
    handlersRef.current = handlers;
  }, [handlers]);

  useEffect(() => {
    // Setup connection status handler
    const connectionHandler = (connected: boolean) => {
      setIsConnected(connected);
      if (connected) {
        setConnectionId(socketService.getConnectionId());
        setLastError(null);
      } else {
        setConnectionId(undefined);
      }
    };

    // Setup error handler
    const errorHandler = (error: string) => {
      setLastError(error);
    };

    // Combine with user handlers
    const allHandlers: SocketEventHandlers = {
      ...handlersRef.current,
      onConnectionStatus: (connected) => {
        connectionHandler(connected);
        handlersRef.current?.onConnectionStatus?.(connected);
      },
      onError: (error) => {
        errorHandler(error);
        handlersRef.current?.onError?.(error);
      },
    };

    // Set handlers on socket service
    socketService.setHandlers(allHandlers);

    // Initial connection status
    setIsConnected(socketService.isConnected());
    setConnectionId(socketService.getConnectionId());

    // Cleanup on unmount
    return () => {
      // Don't disconnect the socket, just remove our handlers
      // The socket service is a singleton and may be used by other components
    };
  }, []);

  const sendMessage = useCallback(
    (message: string, sender: string = "User") => {
      socketService.sendMessage(message, sender);
    },
    []
  );

  const requestDashboardUpdate = useCallback(() => {
    socketService.requestDashboardUpdate();
  }, []);

  const joinRoom = useCallback((room: string) => {
    socketService.joinRoom(room);
  }, []);

  const leaveRoom = useCallback((room: string) => {
    socketService.leaveRoom(room);
  }, []);

  const ping = useCallback(async (): Promise<number> => {
    try {
      return await socketService.ping();
    } catch (error) {
      throw new Error(
        `Ping failed: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    }
  }, []);

  const reconnect = useCallback(() => {
    socketService.forceReconnect();
  }, []);

  return {
    isConnected,
    connectionId,
    sendMessage,
    requestDashboardUpdate,
    joinRoom,
    leaveRoom,
    ping,
    reconnect,
    lastError,
  };
};

/**
 * Hook for real-time dashboard updates
 */
export const useRealTimeDashboard = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [cases, setCases] = useState<PatientCase[]>([]);
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Function to fetch fresh data from API
  const fetchDashboardData = async () => {
    try {
      console.log("🔄 Fetching fresh dashboard data...");
      
      // Import API service
      const { api } = await import("../services/api");
      
      // Fetch metrics
      const metricsResponse = await api.getDashboardMetrics();
      if (metricsResponse) {
        setMetrics(metricsResponse);
        console.log("📊 Metrics updated:", metricsResponse);
      }
      
      // Fetch cases
      const casesResponse = await api.getActiveCases();
      if (casesResponse) {
        setCases(casesResponse);
        console.log("📋 Cases updated:", casesResponse.length, "cases");
      }
      
      // Fetch activities
      const activitiesResponse = await api.getRecentActivity();
      if (activitiesResponse) {
        setActivities(activitiesResponse);
        console.log("📝 Activities updated:", activitiesResponse.length, "activities");
      }
      
      setLastUpdate(new Date());
      
    } catch (error) {
      console.error("❌ Error fetching dashboard data:", error);
    }
  };

  const handlers: SocketEventHandlers = {
    onPatientArrival: (data) => {
      console.log("📥 New patient arrival:", data);
      // Trigger fresh data fetch
      fetchDashboardData();
    },

    onProtocolActivation: (data) => {
      console.log("🚨 Protocol activated:", data);
      // Update case status or add activity
      const newActivity: ActivityEntry = {
        id: `protocol_${Date.now()}`,
        timestamp: new Date(),
        type: "System",
        message: `${data.protocol} protocol activated for ${data.patientId}`,
        status: "In Progress",
        caseId: data.patientId,
      };
      setActivities((prev) => [newActivity, ...prev.slice(0, 19)]);
      setLastUpdate(new Date());
    },

    onCaseUpdate: (data) => {
      console.log("📋 Case updated:", data);
      // Trigger fresh data fetch for case updates
      fetchDashboardData();
    },

    onDashboardUpdate: (data) => {
      console.log("📊 Dashboard updated:", data);
      // Trigger fresh data fetch
      fetchDashboardData();
    },

    onDashboardRefresh: (data) => {
      console.log("🔄 Dashboard refresh requested:", data);
      // Immediately fetch fresh data from API
      fetchDashboardData();
    },

    onAgentActivity: (data) => {
      console.log("⚡ Agent activity:", data);
      // Add agent activity to activity log
      const newActivity: ActivityEntry = {
        id: `agent_${Date.now()}`,
        timestamp: new Date(),
        type: "Agent",
        message: data.message || "Agent activity",
        status: "Complete",
        agentName: data.agent,
      };
      setActivities((prev) => [newActivity, ...prev.slice(0, 19)]);
      setLastUpdate(new Date());
    },
  };

  const { isConnected, sendMessage, lastError } = useSocket(handlers);

  // Initial data fetch on mount
  useEffect(() => {
    fetchDashboardData();
  }, []);

  return {
    metrics,
    cases,
    activities,
    lastUpdate,
    isConnected,
    sendMessage,
    lastError,
    setMetrics,
    setCases,
    setActivities,
    refreshData: fetchDashboardData,
  };
};

/**
 * Hook for real-time chat functionality
 */
export const useRealTimeChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isTyping, setIsTyping] = useState(false);

  const handlers: SocketEventHandlers = {
    onChatMessage: (message) => {
      console.log("💬 New chat message:", message);
      setMessages((prev) => [...prev, message]);

      // Increment unread count if message is from agent
      if (message.type === "agent") {
        setUnreadCount((prev) => prev + 1);
      }
    },

    onAgentMessage: (data) => {
      console.log("🤖 Agent message:", data);
      if (data.message) {
        const chatMessage: ChatMessage = {
          ...data.message,
          timestamp: new Date(data.message.timestamp),
        };
        setMessages((prev) => [...prev, chatMessage]);
        setUnreadCount((prev) => prev + 1);
      }
    },
  };

  const {
    isConnected,
    sendMessage: socketSendMessage,
    lastError,
  } = useSocket(handlers);

  const sendMessage = useCallback(
    (message: string) => {
      socketSendMessage(message, "User");

      // Add user message to local state immediately
      const userMessage: ChatMessage = {
        id: `user_${Date.now()}`,
        content: message,
        timestamp: new Date(),
        sender: "User",
        type: "user",
      };
      setMessages((prev) => [...prev, userMessage]);
    },
    [socketSendMessage]
  );

  const markAsRead = useCallback(() => {
    setUnreadCount(0);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setUnreadCount(0);
  }, []);

  return {
    messages,
    unreadCount,
    isTyping,
    isConnected,
    sendMessage,
    markAsRead,
    clearMessages,
    lastError,
  };
};

export default useSocket;
