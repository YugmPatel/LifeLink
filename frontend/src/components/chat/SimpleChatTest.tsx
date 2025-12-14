import React, { useState } from "react";
import { Send } from "lucide-react";

interface SimpleChatTestProps {
  onSendMessage: (message: string) => void;
  isConnected: boolean;
}

const SimpleChatTest: React.FC<SimpleChatTestProps> = ({
  onSendMessage,
  isConnected,
}) => {
  const [inputMessage, setInputMessage] = useState("");
  const [testMessages, setTestMessages] = useState<
    Array<{ id: string; content: string; sender: string; timestamp: Date }>
  >([
    {
      id: "1",
      content: "Chat system initialized. Send a message to test!",
      sender: "System",
      timestamp: new Date(),
    },
  ]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim()) {
      // Add user message immediately
      const userMessage = {
        id: `user_${Date.now()}`,
        content: inputMessage.trim(),
        sender: "User",
        timestamp: new Date(),
      };

      setTestMessages((prev) => [...prev, userMessage]);

      // Call the parent handler
      onSendMessage(inputMessage.trim());

      // Clear input
      setInputMessage("");

      // Simulate agent response after delay
      setTimeout(() => {
        const agentResponse = {
          id: `agent_${Date.now()}`,
          content: `Received your message: "${userMessage.content}". Processing request...`,
          sender: "ED Coordinator",
          timestamp: new Date(),
        };
        setTestMessages((prev) => [...prev, agentResponse]);
      }, 1500);
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg flex flex-col h-[600px]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">Chat Test</h3>
        <div
          className={`w-2 h-2 rounded-full ${
            isConnected ? "bg-green-500" : "bg-red-500"
          }`}
        ></div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {testMessages.map((message) => (
          <div key={message.id} className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-medium text-gray-300">
                {message.sender.charAt(0).toUpperCase()}
              </span>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-sm font-medium text-blue-400">
                  {message.sender}
                </span>
                <span className="text-xs text-gray-500">
                  {message.timestamp.toLocaleTimeString("en-US", {
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                  })}
                </span>
              </div>

              <div className="text-sm text-gray-300">{message.content}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Input - Fixed Layout */}
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
    </div>
  );
};

export default SimpleChatTest;
