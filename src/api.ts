import type { Department, Issue, Notice, Role } from './types';

const departments: Department[] = [
  'Electrical',
  'Civil and Roads',
  'Plumbing and Water',
  'Sanitation and Housekeeping',
  'Mess and Food',
  'Hostel and Warden',
  'IT and Network',
  'Other'
];

export interface IssueInput {
  title: string;
  description: string;
  category: Department;
  location: string;
  evidence?: string;
}

export interface IssueDraft {
  title?: string;
  description?: string;
  category?: Department;
  location?: string;
}

export interface IssueChatResponse {
  reply?: string;
  draft: IssueDraft;
  confidence?: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: string;
  name: string;
}

export interface DepartmentRecord {
  id: number;
  name: string;
  sla_hours: number;
}

export interface StaffRecord {
  id: string;
  name: string;
  role: string;
  department_id: number | null;
}

export interface AuditRecord {
  id: string;
  at: string;
  actor: string;
  action: string;
  issueId: string;
  detail: string;
}

const AUTH_TOKEN_KEY = 'ca-access-token';

export function getAccessToken(): string | null {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAccessToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(AUTH_TOKEN_KEY, token);
    else localStorage.removeItem(AUTH_TOKEN_KEY);
  } catch {
    throw new Error('Unable to store the sign-in session in this browser.');
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers
    }
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown } | null;
    const detail = typeof body?.detail === 'string' ? body.detail : response.statusText;
    throw new Error(`API request failed (${response.status}): ${detail}`);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function isIssue(value: unknown): value is Issue {
  if (!value || typeof value !== 'object') return false;
  const issue = value as Record<string, unknown>;
  return typeof issue.id === 'string'
    && typeof issue.title === 'string'
    && typeof issue.description === 'string'
    && typeof issue.category === 'string'
    && typeof issue.location === 'string'
    && typeof issue.status === 'string'
    && typeof issue.createdAt === 'string'
    && Array.isArray(issue.updates);
}

function requireIssue(value: unknown): Issue {
  if (!isIssue(value)) {
    throw new Error('The API returned an invalid issue response.');
  }
  return value;
}

export async function fetchIssues(): Promise<Issue[]> {
  const response = await request<unknown>('/issues');
  if (!Array.isArray(response) || !response.every(isIssue)) {
    throw new Error('The API returned an invalid issue list.');
  }
  return response;
}

export async function createIssue(input: IssueInput): Promise<Issue> {
  return requireIssue(await request<unknown>('/issues', {
    method: 'POST',
    body: JSON.stringify(input)
  }));
}

export async function login(scholarNo: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ scholar_no: scholarNo, password })
  });
}

export async function loginDemo(role: Role): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/demo-login', {
    method: 'POST',
    body: JSON.stringify({ role })
  });
}

export async function updateIssueStatus(
  token: string,
  status: string,
  note: string
): Promise<Issue> {
  return requireIssue(await request<unknown>(`/issues/${encodeURIComponent(token)}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status, note })
  }));
}

export async function assignIssue(
  token: string,
  department: string,
  staffName: string
): Promise<Issue> {
  return requireIssue(await request<unknown>(`/issues/${encodeURIComponent(token)}/assignment`, {
    method: 'PATCH',
    body: JSON.stringify({ department, staff_name: staffName })
  }));
}

export async function linkDuplicate(token: string, parentId: string): Promise<Issue> {
  return requireIssue(await request<unknown>(`/issues/${encodeURIComponent(token)}/duplicates`, {
    method: 'POST',
    body: JSON.stringify({ duplicate_of: parentId })
  }));
}

export async function fetchStaffForDepartment(name: string): Promise<StaffRecord[]> {
  const departments = await request<DepartmentRecord[]>('/departments');
  const department = departments.find(item => item.name === name);
  if (!department) throw new Error(`Unknown department: ${name}`);
  return request<StaffRecord[]>(`/departments/${department.id}/staff`);
}

export async function fetchNotifications(): Promise<Notice[]> {
  const result = await request<Array<{ id: number; text: string; at: string; read: boolean; issueId?: string }>>('/notifications');
  return result.map(item => ({ ...item, id: String(item.id) }));
}

export async function markNotificationRead(id: string): Promise<Notice> {
  const item = await request<{ id: number; text: string; at: string; read: boolean; issueId?: string }>(
    `/notifications/${encodeURIComponent(id)}`,
    { method: 'PATCH' }
  );
  return { ...item, id: String(item.id) };
}

export async function fetchAudit(): Promise<AuditRecord[]> {
  return request<AuditRecord[]>('/audit');
}

export async function sendIssueChatMessage(
  message: string,
  draft: IssueDraft
): Promise<IssueChatResponse> {
  const response = await request<unknown>('/issues/chat', {
    method: 'POST',
    body: JSON.stringify({ message, draft })
  });

  if (!response || typeof response !== 'object') {
    throw new Error('The assistant returned an invalid response.');
  }
  const result = response as Record<string, unknown>;
  if (!result.draft || typeof result.draft !== 'object') {
    throw new Error('The assistant response did not include a draft.');
  }

  const returnedDraft = result.draft as Record<string, unknown>;
  if (returnedDraft.category !== undefined
    && (typeof returnedDraft.category !== 'string'
      || !departments.includes(returnedDraft.category as Department))) {
    throw new Error('The assistant returned an invalid complaint category.');
  }

  return {
    reply: typeof result.reply === 'string' ? result.reply : undefined,
    confidence: typeof result.confidence === 'number' ? result.confidence : undefined,
    draft: {
      title: typeof returnedDraft.title === 'string' ? returnedDraft.title : undefined,
      description: typeof returnedDraft.description === 'string' ? returnedDraft.description : undefined,
      category: returnedDraft.category as Department | undefined,
      location: typeof returnedDraft.location === 'string' ? returnedDraft.location : undefined
    }
  };
}
