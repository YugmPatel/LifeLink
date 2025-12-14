/**
 * Socket.IO Service for Real-time Communication
 * Handles WebSocket connections with the FastAPI backend
 */

import { io, Socket } from "socket.io-client";
import {
  PatientCase,
  ChatMessage,
  ActivityEntry,
  WebSocketEvent,
  PatientArrivalEvent,
  ProtocolActivationEvent,
  CaseUpdateEvent,
  AgentMessageEvent,
} from "./types";

const WS_URL = import.meta.env.VITE_WS_URL || "http://localhost:8080";

export interface SocketEventHandlers {
  onPatientArrival?: (data: PatientArrivalEvent["data"]) => void;
  onProtocolActivation?: (data: ProtocolActivationEvent["data"]) => void;
  onCaseUpdate?: (data: CaseUpdateEvent["data"]) => void;
  onAgentMessage?: (data: AgentMessageEvent["data"]) => void;
  onChatMessage?: (message: ChatMessage) => void;
  onDashboardUpdate?: (data: any) => void;
  onDashboardRefresh?: (data: any) => void;
  onAgentActivity?: (data: any) => void;
  onConnectionStatus?: (connected: boolean) => void;
  onError?: (error: string) => void;
}

class SocketService {
  private socket: Socket | null = null;
  private handlers: SocketEventHandlers = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor() {
    this.connect();
  }

  connect(): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    console.log("🔌 Connecting to WebSocket server...");

    this.socket = io(WS_URL, {
      transports: ["websocket", "polling"],
      timeout: 10000,
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });

    this.setupEventHandlers();
    return this.socket;
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on("connect", () => {
      console.log("✅ Connected to WebSocket server");
      this.reconnectAttempts = 0;
      this.handlers.onConnectionStatus?.(true);
    });

    this.socket.on("disconnect", (reason) => {
      console.log("❌ Disconnected from WebSocket server:", reason);
      this.handlers.onConnectionStatus?.(false);
    });

    this.socket.on("connect_error", (error) => {
      console.error("🔥 WebSocket connection error:", error);
      this.reconnectAttempts++;
      this.handlers.onError?.(`Connection failed: ${error.message}`);
    });

    this.socket.on("reconnect", (attemptNumber) => {
      console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
      this.handlers.onConnectionStatus?.(true);
    });

    this.socket.on("reconnect_failed", () => {
      console.error("💥 Failed to reconnect to WebSocket server");
      this.handlers.onError?.("Failed to reconnect to server");
    });

    // Custom events
    this.socket.on("connection_status", (data) => {
      console.log("📡 Connection status:", data);
    });

    this.socket.on("patient_arrival", (data: PatientArrivalEvent) => {
      console.log("🚑 Patient arrival:", data);
      this.handlers.onPatientArrival?.(data.data);
    });

    this.socket.on("protocol_activation", (data: ProtocolActivationEvent) => {
      console.log("🚨 Protocol activation:", data);
      this.handlers.onProtocolActivation?.(data.data);
    });

    this.socket.on("case_update", (data: CaseUpdateEvent) => {
      console.log("📋 Case update:", data);
      this.handlers.onCaseUpdate?.(data.data);
    });

    this.socket.on("agent_message", (data: AgentMessageEvent) => {
      console.log("🤖 Agent message:", data);
      this.handlers.onAgentMessage?.(data.data);
    });

    this.socket.on("chat_message", (message: any) => {
      console.log("💬 Chat message:", message);
      const chatMessage: ChatMessage = {
        ...message,
        timestamp: new Date(message.timestamp),
      };
      this.handlers.onChatMessage?.(chatMessage);
    });

    this.socket.on("dashboard_update", (data: any) => {
      console.log("📊 Dashboard update:", data);
      this.handlers.onDashboardUpdate?.(data.data);
    });

    this.socket.on("dashboard_refresh", (data: any) => {
      console.log("🔄 Dashboard refresh:", data);
      this.handlers.onDashboardRefresh?.(data);
    });

    this.socket.on("agent_activity", (data: any) => {
      console.log("⚡ Agent activity:", data);
      this.handlers.onAgentActivity?.(data.data);
    });

    this.socket.on("message_history", (data: any) => {
      console.log("📜 Message history received:", data);
      if (data.messages && this.handlers.onChatMessage) {
        data.messages.forEach((msg: any) => {
          const chatMessage: ChatMessage = {
            ...msg,
            timestamp: new Date(msg.timestamp),
          };
          this.handlers.onChatMessage?.(chatMessage);
        });
      }
    });

    this.socket.on("error", (error: any) => {
      console.error("🔥 Socket error:", error);
      this.handlers.onError?.(error.message || "Socket error occurred");
    });
  }

  disconnect(): void {
    if (this.socket) {
      console.log("🔌 Disconnecting from WebSocket server...");
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // Event handler registration
  setHandlers(handlers: SocketEventHandlers): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  addHandler<K extends keyof SocketEventHandlers>(
    event: K,
    handler: SocketEventHandlers[K]
  ): void {
    this.handlers[event] = handler;
  }

  removeHandler<K extends keyof SocketEventHandlers>(event: K): void {
    delete this.handlers[event];
  }

  // Emit events to server
  sendMessage(message: string, sender: string = "User"): void {
    if (this.socket?.connected) {
      this.socket.emit("send_message", {
        message,
        sender,
        timestamp: new Date().toISOString(),
      });
    } else {
      console.warn("⚠️ Cannot send message: not connected to server");
      this.handlers.onError?.("Not connected to server");
    }
  }

  requestDashboardUpdate(): void {
    if (this.socket?.connected) {
      this.socket.emit("request_dashboard_update");
    }
  }

  joinRoom(room: string): void {
    if (this.socket?.connected) {
      this.socket.emit("join_room", { room });
    }
  }

  leaveRoom(room: string): void {
    if (this.socket?.connected) {
      this.socket.emit("leave_room", { room });
    }
  }

  // Connection status
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getConnectionId(): string | undefined {
    return this.socket?.id;
  }

  // Utility methods
  ping(): Promise<number> {
    return new Promise((resolve, reject) => {
      if (!this.socket?.connected) {
        reject(new Error("Not connected"));
        return;
      }

      const start = Date.now();
      this.socket.emit("ping", start, (response: number) => {
        const latency = Date.now() - start;
        resolve(latency);
      });

      // Timeout after 5 seconds
      setTimeout(() => {
        reject(new Error("Ping timeout"));
      }, 5000);
    });
  }

  // Force reconnection
  forceReconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      setTimeout(() => {
        this.connect();
      }, 1000);
    }
  }
}

// Create singleton instance
export const socketService = new SocketService();

// Export convenience functions
export const useSocket = () => {
  return {
    socket: socketService,
    isConnected: socketService.isConnected(),
    sendMessage: (message: string, sender?: string) =>
      socketService.sendMessage(message, sender),
    setHandlers: (handlers: SocketEventHandlers) =>
      socketService.setHandlers(handlers),
    disconnect: () => socketService.disconnect(),
    reconnect: () => socketService.forceReconnect(),
  };
};

export default socketService;
