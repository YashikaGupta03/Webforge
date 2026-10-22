export type IssueStatus = 'Submitted' | 'Read/Verified' | 'Assigned' | 'In Progress' | 'Resolved' | 'Reopened';
export type Priority = 'Critical' | 'High' | 'Medium' | 'Low';
export type Department = 'Electrical' | 'Civil and Roads' | 'Plumbing and Water' | 'Sanitation and Housekeeping' | 'Mess and Food' | 'Hostel and Warden' | 'IT and Network' | 'Other';
export type Role = 'Student' | 'Warden' | 'Administrator' | 'Department Staff' | 'Super Admin';
export interface Issue {
  id: string; title: string; description: string; category: Department; location: string;
  priority: Priority; score: number; safety: number; severity: number; impact: number;
  waiting: number; related: number; confidence: number; status: IssueStatus;
  createdAt: string; assignedTo: string; department: string; duplicateOf?: string;
  updates: { at: string; status: IssueStatus; note: string }[];
  evidence?: string; createdBy: string; slaHours: number;
}
export interface Notice { id: string; text: string; at: string; read: boolean; issueId?: string; }
