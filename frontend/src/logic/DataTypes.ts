export interface TaskStatus {
    id: string;
    name: string;
    color?: string;
}

export const defaultStatuses: TaskStatus[] = [
    { id: 'todo', name: 'Todo', color: '#9ca3af' },
    { id: 'in-progress', name: 'In Progress', color: '#3b82f6' },
    { id: 'done', name: 'Done', color: '#22c55e' },
];


export interface Label {
    id?: string;
    name: string;
    color: string;
}

export interface TaskProps {
    id?: string;
    title: string;
    description: string;
    status: TaskStatus;
    dateCreated: Date;
    dateDue?: Date;
    labels: Label[];
    onEdit?: (t: TaskProps) => void;
    onDelete?: (id: string) => void;
    isExpanded?: boolean;
    onToggleExpand?: () => void;
    priority?: number;
}

// Enum types matching backend
export enum CrimeType {
  TYPE_3 = "TYPE_3", 
  TYPE_2 = "TYPE_2", 
  TYPE_1 = "TYPE_1", 
  CRITICAL = "CRITICAL", // 
}

export enum ComplainStatus {
  DRAFT = "DRAFT", 
  PENDING_CADET = "PENDING_CADET",
  RETURNED_TO_COMPLAINANT = "RETURNED_TO_COMPLAINANT", 
  PENDING_OFFICER = "PENDING_OFFICER", 
  APPROVED = "APPROVED", 
  REJECTED = "REJECTED",
  CANCELLED = "CANCELLED", 
}

export enum ComplainantStatus {
  PENDING = "PENDING", 
  APPROVED = "APPROVED", 
  REJECTED = "REJECTED", 
}

export interface RegisterComplain {
  id: string;
  creator: User | string; 
  title: string;
  description: string;
  incident_datetime: string; 
  incident_location: string;
  crime_type: CrimeType;
  created_at: string;
  updated_at: string;
  status: ComplainStatus;
  revision_count: number;
  max_revisions: number;
  
  can_be_edited_by_complainant?: boolean;
  can_submit?: boolean;
  
  complainants?: Complainant[];
  reviews?: ComplainReview[];
}


export interface User {
  id: string;
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
}

// Interface for Complainant model
export interface Complainant {
  id?: string; // Note: The model doesn't show an ID field, but Django creates one automatically
  complain?: string | RegisterComplain; // ID or object
  case?: string | Case; // ID or object
  user: User | string;
  relationship_to_incident: string;
  status: ComplainantStatus;
  created_at: string;
}

// Interface for ComplainReview model
export interface ComplainReview {
  id?: string;
  complain: string | RegisterComplain;
  reviewed_by: User | string;
  reviewed_at: string;
  message: string;
  is_approval: boolean;
  to_status: ComplainStatus;
}

// Interface for Case (referenced in Complainant)
export interface Case {
  id: string;
  // Add other Case fields as needed
  title?: string;
  case_number?: string;
}

// Props interface for a PreComplain component
export interface PreComplainProps {
  id?: string;
  complain?: RegisterComplain;
  isLoading?: boolean;
  error?: string | null;
  onSubmit?: (data: Partial<RegisterComplain>) => void | Promise<void>;
  onCancel?: () => void;
  mode?: 'create' | 'edit' | 'view';
  readOnly?: boolean;
}

// Interface for creating/updating a complain (subset of fields that can be edited)
export interface RegisterComplainFormData {
  title: string;
  description: string;
  incident_datetime: string;
  incident_location: string;
  crime_type: CrimeType;
  complainants?: Omit<Complainant, 'id' | 'created_at' | 'status'>[];
}

// Interface for API response when fetching a complain
export interface RegisterComplainApiResponse {
  data: RegisterComplain;
  message?: string;
  success: boolean;
}

// Interface for API response when fetching list of complains
export interface RegisterComplainListApiResponse {
  data: RegisterComplain[];
  count: number;
  next?: string;
  previous?: string;
  success: boolean;
}

// Interface for review submission
export interface ComplainReviewSubmitData {
  message: string;
  is_approval: boolean;
  to_status: ComplainStatus;
}