import React, { useState, useRef, useEffect } from "react";
import { Send, MessageSquare, Minimize2, Maximize2 } from "lucide-react";
import { ChatMessage } from "../../services/types";

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isConnected: boolean;
  className?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages: initialMessages,
  onSendMessage,
  isConnected,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [inputMessage, setInputMessage] = useState("");
  const [localMessages, setLocalMessages] =
    useState<ChatMessage[]>(initialMessages);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Update local messages when props change
  useEffect(() => {
    setLocalMessages(initialMessages);
  }, [initialMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [localMessages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim()) {
      console.log("Sending message:", inputMessage.trim());

      // Add user message immediately to local state
      const userMessage: ChatMessage = {
        id: `user_${Date.now()}`,
        content: inputMessage.trim(),
        timestamp: new Date(),
        sender: "User",
        type: "user",
      };

      setLocalMessages((prev) => [...prev, userMessage]);

      // Call parent handler (this will try WebSocket, fallback to mock)
      onSendMessage(inputMessage.trim());

      // Clear input
      setInputMessage("");

      // Simulate agent response if WebSocket isn't working
      setTimeout(() => {
        const responses = [
          "Message received. Processing request...",
          "Acknowledged. Coordinating with relevant departments.",
          "Request understood. Initiating appropriate protocols.",
          "Confirmed. Updating patient status and notifying team.",
          "Received. Checking resource availability and scheduling.",
        ];

        const randomResponse =
          responses[Math.floor(Math.random() * responses.length)];

        const agentMessage: ChatMessage = {
          id: `agent_${Date.now()}`,
          content: randomResponse,
          timestamp: new Date(),
          sender: "ED Coordinator",
          type: "agent",
          agentType: "ed_coordinator",
        };

        setLocalMessages((prev) => [...prev, agentMessage]);
      }, 1500);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  const getAgentColor = (agentType?: ChatMessage["agentType"]) => {
    const colors = {
      ed_coordinator: "text-blue-400",
      resource_manager: "text-green-400",
      specialist_coordinator: "text-purple-400",
      lab_service: "text-yellow-400",
      pharmacy: "text-pink-400",
      bed_management: "text-cyan-400",
    };
    return agentType ? colors[agentType] || "text-gray-400" : "text-gray-400";
  };

  return (
    <div
      className={`bg-gray-900 border border-gray-700 rounded-lg flex flex-col ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 flex-shrink-0">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Chat</h3>
          {!isConnected && (
            <span className="text-xs text-red-400 bg-red-900/20 px-2 py-1 rounded">
              Disconnected
            </span>
          )}
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-gray-400 hover:text-white transition-colors"
        >
          {isOpen ? (
            <Minimize2 className="w-4 h-4" />
          ) : (
            <Maximize2 className="w-4 h-4" />
          )}
        </button>
      </div>

      {isOpen && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
            {localMessages.map((message) => (
              <div key={message.id} className="slide-in-right">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                      <span className="text-xs font-medium text-gray-300">
                        {message.sender.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span
                        className={`text-sm font-medium ${getAgentColor(
                          message.agentType
                        )}`}
                      >
                        {message.sender}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>

                    <div className="text-sm text-gray-300 whitespace-pre-wrap">
                      {message.content}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input - Fixed Container */}
          <div className="p-4 border-t border-gray-700 flex-shrink-0">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={isConnected ? "Type a message" : "Disconnected..."}
                disabled={!isConnected}
                className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm min-w-0"
              />
              <button
                type="submit"
                disabled={!inputMessage.trim() || !isConnected}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-3 py-2 rounded-lg transition-colors flex items-center justify-center flex-shrink-0 w-16"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </>
      )}

      {/* Activity Feed (when minimized) */}
      {!isOpen && localMessages.length > 0 && (
        <div className="p-4">
          <div className="space-y-2">
            {localMessages.slice(-3).map((message) => (
              <div key={message.id} className="text-xs text-gray-400 truncate">
                <span className={getAgentColor(message.agentType)}>
                  {message.sender}:
                </span>{" "}
                {message.content}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatInterface;
