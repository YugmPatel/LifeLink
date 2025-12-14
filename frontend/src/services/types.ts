// Core data types for EDFlow AI Dashboard
import { ReactNode } from "react";

export interface PatientVitals {
  hr: number; // heart rate
  bp_sys: number; // systolic BP
  bp_dia: number; // diastolic BP
  spo2: number; // oxygen saturation
  temp?: number; // temperature
}

export interface PatientCase {
  id: string;
  type: "STEMI" | "Stroke" | "Trauma" | "General" | "Pediatric";
  duration: number; // minutes since arrival
  vitals: PatientVitals;
  status:
    | "Arriving"
    | "Triaged"
    | "In Treatment"
    | "Pending"
    | "Admitted"
    | "Discharged";
  location: string;
  labETA?: number; // minutes
  assignedBed?: string;
  priority: 1 | 2 | 3 | 4 | 5; // 1 = critical, 5 = minimal
  timestamp: Date;
  chiefComplaint?: string;
  emsReport?: string;
}

export interface DashboardMetrics {
  active_cases: number;
  avg_lab_eta: number; // minutes
  icu_beds_held: number;
  doctors_paged: number;
  last_updated: Date;
}

export interface ActivityEntry {
  id: string;
  timestamp: Date;
  type: "Lab" | "Pharm" | "Bed" | "Doctor" | "System" | "Agent";
  message: string;
  status: "Ready" | "Pending" | "Complete" | "Failed" | "In Progress";
  caseId?: string;
  agentName?: string;
  priority?: "High" | "Medium" | "Low";
}

export interface ChatMessage {
  id: string;
  content: string;
  timestamp: Date;
  sender: string;
  type: "user" | "agent" | "system";
  agentType?:
    | "ed_coordinator"
    | "resource_manager"
    | "specialist_coordinator"
    | "lab_service"
    | "pharmacy"
    | "bed_management";
}

export interface AgentStatus {
  name: string;
  type: string;
  status: "online" | "offline" | "busy";
  lastSeen: Date;
  address: string;
  messageCount: number;
}

export interface SimulationResponse {
  message: string;
  patientId: string;
  timestamp: Date;
  success: boolean;
}

// WebSocket event types
export interface WebSocketEvent {
  type: string;
  data: any;
  timestamp: string;
}

export interface PatientArrivalEvent extends WebSocketEvent {
  type: "patient_arrival";
  data: {
    case: PatientCase;
    protocol?: string;
  };
}

export interface ProtocolActivationEvent extends WebSocketEvent {
  type: "protocol_activation";
  data: {
    patientId: string;
    protocol: string;
    activationTime: string;
    targetCompletion: string;
  };
}

export interface CaseUpdateEvent extends WebSocketEvent {
  type: "case_update";
  data: {
    caseId: string;
    updates: Partial<PatientCase>;
  };
}

export interface AgentMessageEvent extends WebSocketEvent {
  type: "agent_message";
  data: {
    message: ChatMessage;
  };
}

export interface ResourceUpdateEvent extends WebSocketEvent {
  type: "resource_update";
  data: {
    resourceType: string;
    resourceId: string;
    status: string;
    caseId?: string;
  };
}

export interface LabResultEvent extends WebSocketEvent {
  type: "lab_result";
  data: {
    caseId: string;
    testName: string;
    result: string;
    critical: boolean;
  };
}

export interface MedicationReadyEvent extends WebSocketEvent {
  type: "medication_ready";
  data: {
    caseId: string;
    medication: string;
    status: string;
  };
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  statusCode: number;
  timestamp: string;
}

// Store state types
export interface DashboardState {
  metrics: DashboardMetrics;
  activeCases: PatientCase[];
  activityLog: ActivityEntry[];
  isConnected: boolean;
  lastUpdate: Date;
  loading: boolean;
  error: string | null;
}

export interface ChatState {
  messages: ChatMessage[];
  isOpen: boolean;
  unreadCount: number;
  typing: boolean;
  connected: boolean;
}

export interface AgentState {
  agents: AgentStatus[];
  selectedAgent: string | null;
  communicationLog: ChatMessage[];
}

// Component prop types
export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: "up" | "down" | "stable";
  color?: "blue" | "green" | "red" | "yellow";
}

export interface CaseCardProps {
  case: PatientCase;
  onClick?: (caseId: string) => void;
  className?: string;
}

export interface ActivityLogProps {
  entries: ActivityEntry[];
  filter?: "all" | "Lab" | "Pharm" | "Bed" | "Doctor" | "System";
  maxEntries?: number;
}

export interface ChatInterfaceProps {
  isOpen: boolean;
  onToggle: () => void;
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  className?: string;
}

// Utility types
export type CaseType = PatientCase["type"];
export type CaseStatus = PatientCase["status"];
export type ActivityType = ActivityEntry["type"];
export type ActivityStatus = ActivityEntry["status"];
export type MessageType = ChatMessage["type"];
export type AgentType = AgentStatus["type"];

// Constants
export const CASE_TYPES: CaseType[] = [
  "STEMI",
  "Stroke",
  "Trauma",
  "General",
  "Pediatric",
];
export const CASE_STATUSES: CaseStatus[] = [
  "Arriving",
  "Triaged",
  "In Treatment",
  "Pending",
  "Admitted",
  "Discharged",
];
export const ACTIVITY_TYPES: ActivityType[] = [
  "Lab",
  "Pharm",
  "Bed",
  "Doctor",
  "System",
  "Agent",
];
export const ACTIVITY_STATUSES: ActivityStatus[] = [
  "Ready",
  "Pending",
  "Complete",
  "Failed",
  "In Progress",
];

// Color mappings
export const CASE_TYPE_COLORS: Record<CaseType, string> = {
  STEMI: "red",
  Stroke: "orange",
  Trauma: "red",
  General: "blue",
  Pediatric: "purple",
};

export const PRIORITY_COLORS: Record<number, string> = {
  1: "red", // Critical
  2: "orange", // High
  3: "yellow", // Medium
  4: "blue", // Low
  5: "gray", // Minimal
};

export const STATUS_COLORS: Record<CaseStatus, string> = {
  Arriving: "yellow",
  Triaged: "blue",
  "In Treatment": "green",
  Pending: "orange",
  Admitted: "green",
  Discharged: "gray",
};
