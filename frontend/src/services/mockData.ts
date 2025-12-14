// Mock data service for development and testing
import {
  PatientCase,
  DashboardMetrics,
  ActivityEntry,
  ChatMessage,
  AgentStatus,
} from "./types";

// Generate mock patient cases based on the UI design
export const mockPatientCases: PatientCase[] = [
  {
    id: "CASE-001",
    type: "STEMI",
    duration: 8, // 8 minutes
    vitals: {
      hr: 110,
      bp_sys: 190,
      bp_dia: 895, // This seems like a typo in the original, should be 95
      spo2: 94,
      temp: 37.2,
    },
    status: "In Treatment",
    location: "ED-1",
    labETA: 12,
    assignedBed: "ED-1",
    priority: 1,
    timestamp: new Date(Date.now() - 8 * 60 * 1000), // 8 minutes ago
    chiefComplaint: "Severe chest pain radiating to left arm and jaw",
    emsReport: "72-year-old male with crushing chest pain, ST elevation on ECG",
  },
  {
    id: "CASE-002",
    type: "STEMI",
    duration: 5,
    vitals: {
      hr: 105,
      bp_sys: 145,
      bp_dia: 88,
      spo2: 96,
      temp: 36.8,
    },
    status: "Pending",
    location: "ED-Bed1",
    assignedBed: "ED-Bed1",
    priority: 1,
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    chiefComplaint: "Chest pain with shortness of breath",
    emsReport: "Suspected MI, patient stable",
  },
  {
    id: "CASE-003",
    type: "Stroke",
    duration: 7,
    vitals: {
      hr: 80,
      bp_sys: 195,
      bp_dia: 118,
      spo2: 96,
      temp: 36.5,
    },
    status: "Pending",
    location: "ED-2",
    labETA: 6,
    priority: 1,
    timestamp: new Date(Date.now() - 7 * 60 * 1000),
    chiefComplaint: "Sudden onset weakness and speech difficulty",
    emsReport: "Left-sided weakness, NIHSS 8, suspected stroke",
  },
];

export const mockDashboardMetrics: DashboardMetrics = {
  active_cases: 3,
  avg_lab_eta: 9, // minutes
  icu_beds_held: 2,
  doctors_paged: 2,
  last_updated: new Date(),
};

export const mockActivityEntries: ActivityEntry[] = [
  {
    id: "1",
    timestamp: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
    type: "Lab",
    message: "Lab ETA 12m",
    status: "Pending",
    caseId: "CASE-001",
  },
  {
    id: "2",
    timestamp: new Date(Date.now() - 3 * 60 * 1000),
    type: "Pharm",
    message: "STEMI kit ready",
    status: "Ready",
    caseId: "CASE-001",
  },
  {
    id: "3",
    timestamp: new Date(Date.now() - 4 * 60 * 1000),
    type: "Bed",
    message: "iCU3 held",
    status: "Pending",
    caseId: "CASE-001",
  },
  {
    id: "4",
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    type: "Doctor",
    message: "Dr. Lee paged",
    status: "Complete",
    caseId: "CASE-001",
  },
  {
    id: "5",
    timestamp: new Date(Date.now() - 6 * 60 * 1000),
    type: "Doctor",
    message: "Dr. Patel paged",
    status: "Complete",
    caseId: "CASE-003",
  },
  {
    id: "6",
    timestamp: new Date(Date.now() - 1 * 60 * 1000),
    type: "System",
    message: "STEMI kit ready",
    status: "Ready",
  },
  {
    id: "7",
    timestamp: new Date(Date.now() - 30 * 1000), // 30 seconds ago
    type: "System",
    message: "ED-Bed2 assigned",
    status: "Complete",
  },
];

export const mockChatMessages: ChatMessage[] = [
  {
    id: "1",
    content: "Prep STEMI (ETA 8m)",
    timestamp: new Date(Date.now() - 8 * 60 * 1000),
    sender: "ED Coordinator",
    type: "agent",
    agentType: "ed_coordinator",
  },
  {
    id: "2",
    content: "Orcpl STEMI activation",
    timestamp: new Date(Date.now() - 7 * 60 * 1000),
    sender: "Specialist Coordinator",
    type: "agent",
    agentType: "specialist_coordinator",
  },
  {
    id: "3",
    content:
      "STEMI activation\nOrdered freponin STAT\nHeld ICU-2\nPaged Cardiology",
    timestamp: new Date(Date.now() - 6 * 60 * 1000),
    sender: "Resource Manager",
    type: "agent",
    agentType: "resource_manager",
  },
  {
    id: "4",
    content: "Lab ETA 6m",
    timestamp: new Date(Date.now() - 2 * 60 * 1000),
    sender: "Lab Service",
    type: "agent",
    agentType: "lab_service",
  },
  {
    id: "5",
    content: "STEMI kit ready",
    timestamp: new Date(Date.now() - 1 * 60 * 1000),
    sender: "Pharmacy",
    type: "agent",
    agentType: "pharmacy",
  },
];

export const mockAgentStatuses: AgentStatus[] = [
  {
    name: "ED Coordinator",
    type: "ed_coordinator",
    status: "online",
    lastSeen: new Date(),
    address: "agent1qw2e3r4t5y6u7i8o9p0",
    messageCount: 15,
  },
  {
    name: "Resource Manager",
    type: "resource_manager",
    status: "online",
    lastSeen: new Date(Date.now() - 30 * 1000),
    address: "agent2q3w4e5r6t7y8u9i0o1p",
    messageCount: 8,
  },
  {
    name: "Specialist Coordinator",
    type: "specialist_coordinator",
    status: "busy",
    lastSeen: new Date(Date.now() - 60 * 1000),
    address: "agent3w4e5r6t7y8u9i0o1p2q",
    messageCount: 12,
  },
  {
    name: "Lab Service",
    type: "lab_service",
    status: "online",
    lastSeen: new Date(Date.now() - 15 * 1000),
    address: "agent4e5r6t7y8u9i0o1p2q3w",
    messageCount: 6,
  },
  {
    name: "Pharmacy",
    type: "pharmacy",
    status: "online",
    lastSeen: new Date(Date.now() - 45 * 1000),
    address: "agent5r6t7y8u9i0o1p2q3w4e",
    messageCount: 4,
  },
  {
    name: "Bed Management",
    type: "bed_management",
    status: "online",
    lastSeen: new Date(Date.now() - 20 * 1000),
    address: "agent6t7y8u9i0o1p2q3w4e5r",
    messageCount: 3,
  },
];

// Utility functions for generating dynamic mock data
export const generateRandomVitals = (): PatientCase["vitals"] => ({
  hr: Math.floor(Math.random() * 60) + 60, // 60-120
  bp_sys: Math.floor(Math.random() * 80) + 100, // 100-180
  bp_dia: Math.floor(Math.random() * 40) + 60, // 60-100
  spo2: Math.floor(Math.random() * 10) + 90, // 90-100
  temp: Math.round((Math.random() * 4 + 36) * 10) / 10, // 36.0-40.0
});

export const generateMockPatient = (type: PatientCase["type"]): PatientCase => {
  const id = `CASE-${String(Math.floor(Math.random() * 999) + 1).padStart(
    3,
    "0"
  )}`;
  const duration = Math.floor(Math.random() * 30) + 1; // 1-30 minutes

  return {
    id,
    type,
    duration,
    vitals: generateRandomVitals(),
    status: ["Arriving", "Triaged", "In Treatment", "Pending"][
      Math.floor(Math.random() * 4)
    ] as PatientCase["status"],
    location: `ED-${Math.floor(Math.random() * 10) + 1}`,
    labETA: Math.floor(Math.random() * 20) + 5, // 5-25 minutes
    assignedBed: `Bed-${Math.floor(Math.random() * 20) + 1}`,
    priority: (Math.floor(Math.random() * 3) + 1) as 1 | 2 | 3, // 1-3 for emergency cases
    timestamp: new Date(Date.now() - duration * 60 * 1000),
    chiefComplaint: getChiefComplaintByType(type),
    emsReport: getEMSReportByType(type),
  };
};

const getChiefComplaintByType = (type: PatientCase["type"]): string => {
  const complaints = {
    STEMI: "Severe chest pain radiating to left arm",
    Stroke: "Sudden onset weakness and speech difficulty",
    Trauma: "Multiple injuries from motor vehicle accident",
    General: "Abdominal pain and nausea",
    Pediatric: "High fever and difficulty breathing",
  };
  return complaints[type];
};

const getEMSReportByType = (type: PatientCase["type"]): string => {
  const reports = {
    STEMI: "ST elevation on ECG, suspected STEMI",
    Stroke: "Left-sided weakness, NIHSS 8, suspected stroke",
    Trauma: "High-speed MVA, multiple trauma, stable vitals",
    General: "Adult patient with acute abdominal pain",
    Pediatric: "5-year-old with respiratory distress",
  };
  return reports[type];
};

export const addNewMockActivity = (
  type: ActivityEntry["type"],
  message: string,
  caseId?: string
): ActivityEntry => ({
  id: String(Date.now()),
  timestamp: new Date(),
  type,
  message,
  status: "Pending",
  caseId,
});

export const addNewMockMessage = (
  content: string,
  sender: string,
  agentType?: ChatMessage["agentType"]
): ChatMessage => ({
  id: String(Date.now()),
  content,
  timestamp: new Date(),
  sender,
  type: agentType ? "agent" : "user",
  agentType,
});

// Simulate real-time updates
export const simulatePatientArrival = (
  type: PatientCase["type"] = "STEMI"
): PatientCase => {
  return generateMockPatient(type);
};

export const simulateProtocolActivation = (
  patientId: string,
  protocol: string
) => ({
  patientId,
  protocol,
  activationTime: new Date().toISOString(),
  targetCompletion: new Date(Date.now() + 5 * 60 * 1000).toISOString(), // 5 minutes from now
});

// Export all mock data as a single object for easy access
export const mockData = {
  cases: mockPatientCases,
  metrics: mockDashboardMetrics,
  activities: mockActivityEntries,
  messages: mockChatMessages,
  agents: mockAgentStatuses,
};
