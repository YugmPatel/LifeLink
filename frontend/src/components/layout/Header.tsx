import { useState, useEffect } from "react";
import { ChevronDown, Wifi, WifiOff } from "lucide-react";

interface HeaderProps {
  onSimulateSTEMI: () => void;
  onSimulateStroke: () => void;
  isConnected: boolean;
}

const Header: React.FC<HeaderProps> = ({
  onSimulateSTEMI,
  onSimulateStroke,
  isConnected,
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const selectedLocation = "local";

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  return (
    <header className="bg-gray-900 border-b border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left side - Logo and Location */}
        <div className="flex items-center space-x-6">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="medical-cross text-blue-500 text-xl"></div>
            <h1 className="text-xl font-bold text-white">LifeLink</h1>
          </div>

          {/* Location Selector */}
          <div className="relative">
            <button className="flex items-center space-x-2 bg-gray-800 hover:bg-gray-700 px-3 py-2 rounded-lg transition-colors">
              <span className="text-gray-300 text-sm">{selectedLocation}</span>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Center - Title */}
        <div className="flex-1 text-center">
          <h2 className="text-lg font-semibold text-white">
            Instant Emergency, Instant Response
          </h2>
        </div>

        {/* Right side - Actions and Time */}
        <div className="flex items-center space-x-4">
          {/* Simulation Buttons */}
          <button
            onClick={onSimulateSTEMI}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Simulate STEMI
          </button>

          <button
            onClick={onSimulateStroke}
            className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Simulate Stroke
          </button>

          {/* Connection Status */}
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <Wifi className="w-4 h-4 text-green-500" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-500" />
            )}
          </div>

          {/* Current Time */}
          <div className="text-white font-mono text-lg">
            {formatTime(currentTime)}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
