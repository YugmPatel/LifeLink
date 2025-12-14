import React from "react";
import { Users, Clock, Bed, UserCheck } from "lucide-react";
import { DashboardMetrics } from "../../services/types";

interface MetricsCardsProps {
  metrics: DashboardMetrics;
}

const MetricsCards: React.FC<MetricsCardsProps> = ({ metrics }) => {
  const cards = [
    {
      title: "Active Cases",
      value: metrics.active_cases,
      icon: <Users className="w-6 h-6" />,
      color: "text-blue-500",
    },
    {
      title: "Avg Lab ETA",
      value: `${metrics.avg_lab_eta}m`,
      icon: <Clock className="w-6 h-6" />,
      color: "text-green-500",
    },
    {
      title: "ICU Beds Held",
      value: metrics.icu_beds_held,
      icon: <Bed className="w-6 h-6" />,
      color: "text-yellow-500",
    },
    {
      title: "Doctors Paged",
      value: metrics.doctors_paged,
      icon: <UserCheck className="w-6 h-6" />,
      color: "text-purple-500",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-gray-900 border border-gray-700 rounded-lg p-6 card-hover"
        >
          <div className="flex items-center justify-between mb-4">
            <div className={`${card.color}`}>{card.icon}</div>
          </div>

          <div>
            <div className="text-2xl font-bold text-white mb-1">
              {card.value}
            </div>
            <div className="text-sm text-gray-400">{card.title}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MetricsCards;
