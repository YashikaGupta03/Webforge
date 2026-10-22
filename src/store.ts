import { create } from 'zustand';
import { assignIssue as assignIssueRequest, createIssue, fetchAudit, fetchIssues, fetchNotifications, getAccessToken, linkDuplicate, login as loginRequest, loginDemo as loginDemoRequest, markNotificationRead, setAccessToken, updateIssueStatus } from './api';
import type { IssueInput } from './api';
import type { Issue, IssueStatus, Notice, Role } from './types';

const read = <T,>(key: string, fallback: T): T => {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) as T : fallback;
  } catch {
    return fallback;
  }
};

const persist = (key: string, value: unknown) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Browser storage may be unavailable.
  }
};

interface Audit {
  id: string;
  at: string;
  actor: string;
  action: string;
  issueId: string;
  detail: string;
}

interface AppState {
  issues: Issue[];
  issuesLoading: boolean;
  issuesLoadFailed: boolean;
  apiError: string | null;
  role: Role;
  isAuthenticated: boolean;
  notices: Notice[];
  audit: Audit[];
  loadIssues: () => Promise<void>;
  loadNotifications: () => Promise<void>;
  loadAudit: () => Promise<void>;
  clearApiError: () => void;
  login: (scholarNo: string, password: string) => Promise<Role>;
  loginDemo: (role: Role) => Promise<Role>;
  logout: () => void;
  addIssue: (input: IssueInput) => Promise<Issue>;
  updateStatus: (id: string, status: IssueStatus, note: string) => Promise<void>;
  assignIssue: (id: string, department: string, staff: string) => Promise<void>;
  confirmDuplicate: (id: string, parentId: string) => Promise<void>;
  markNoticeRead: (id: string) => void;
  reopenIssue: (id: string, reason: string) => Promise<void>;
}

let issueLoad: Promise<void> | undefined;

function updateIssue(issues: Issue[], updated: Issue): Issue[] {
  return [updated, ...issues.filter(issue => issue.id !== updated.id)];
}

export const useAppStore = create<AppState>((set, get) => ({
  issues: [],
  issuesLoading: false,
  issuesLoadFailed: false,
  apiError: null,
  role: read<Role>('ca-role', 'Administrator'),
  isAuthenticated: Boolean(getAccessToken()),
  notices: [],
  audit: [],

  loadIssues: () => {
    if (issueLoad) return issueLoad;

    set({ issuesLoading: true, issuesLoadFailed: false, apiError: null });
    issueLoad = fetchIssues()
      .then(issues => set({ issues, issuesLoadFailed: false }))
      .catch((error: unknown) => {
        set({
          apiError: error instanceof Error ? error.message : 'Unable to load complaints.',
          issuesLoadFailed: true
        });
      })
      .finally(() => {
        set({ issuesLoading: false });
        issueLoad = undefined;
      });
    return issueLoad;
  },
  loadNotifications: async () => {
    try {
      set({ notices: await fetchNotifications() });
    } catch (error) {
      set({ apiError: error instanceof Error ? error.message : 'Unable to load notifications.' });
    }
  },
  loadAudit: async () => {
    try {
      set({ audit: await fetchAudit() });
    } catch (error) {
      set({ apiError: error instanceof Error ? error.message : 'Unable to load the audit log.' });
    }
  },

  clearApiError: () => set({ apiError: null, issuesLoadFailed: false }),
  login: async (scholarNo, password) => {
    const result = await loginRequest(scholarNo, password);
    const roles: Role[] = ['Student', 'Warden', 'Administrator', 'Department Staff', 'Super Admin'];
    if (!roles.includes(result.role as Role)) {
      throw new Error('The server returned an unsupported account role.');
    }
    setAccessToken(result.access_token);
    persist('ca-role', result.role);
    set({ role: result.role as Role, isAuthenticated: true, apiError: null });
    return result.role as Role;
  },
  loginDemo: async role => {
    const result = await loginDemoRequest(role);
    if (result.role !== role) {
      throw new Error('The server returned a different demo role than requested.');
    }
    setAccessToken(result.access_token);
    persist('ca-role', result.role);
    set({ role, isAuthenticated: true, apiError: null });
    return role;
  },
  logout: () => {
    setAccessToken(null);
    set({ isAuthenticated: false, issues: [], notices: [], audit: [], apiError: null });
  },
  markNoticeRead: async id => {
    try {
      const updated = await markNotificationRead(id);
      set(state => ({ notices: state.notices.map(notice => notice.id === id ? updated : notice) }));
    } catch (error) {
      set({ apiError: error instanceof Error ? error.message : 'Unable to update notification.' });
    }
  },
  addIssue: async input => {
    set({ apiError: null });
    try {
      const issue = await createIssue(input);
      set(state => {
        const issues = updateIssue(state.issues, issue);
        return { issues };
      });
      return issue;
    } catch (error) {
      set({ apiError: error instanceof Error ? error.message : 'Unable to submit complaint.', issuesLoadFailed: false });
      throw error;
    }
  },
  updateStatus: async (id, status, note) => {
    set({ apiError: null });
    try {
      const issue = await updateIssueStatus(id, status, note);
      set(state => {
        const issues = updateIssue(state.issues, issue);
        return { issues };
      });
    } catch (error) {
      set({ apiError: error instanceof Error ? error.message : 'Unable to update complaint status.', issuesLoadFailed: false });
      throw error;
    }
  },
  assignIssue: async (id, department, staff) => {
    set({ apiError: null });
    try {
      const issue = await assignIssueRequest(id, department, staff);
      set(state => {
        const issues = updateIssue(state.issues, issue);
        return { issues };
      });
    } catch (error) {
      set({ apiError: error instanceof Error ? error.message : 'Unable to assign complaint.', issuesLoadFailed: false });
      throw error;
    }
  },
  confirmDuplicate: async (id, parentId) => {
    set({ apiError: null });
    try {
      const issue = await linkDuplicate(id, parentId);
      set(state => {
        const issues = updateIssue(state.issues, issue);
        return { issues };
      });
    } catch (error) {
      set({ apiError: error instanceof Error ? error.message : 'Unable to link duplicate complaint.', issuesLoadFailed: false });
      throw error;
    }
  },
  reopenIssue: (id, reason) => get().updateStatus(id, 'Reopened', `Student reopened issue: ${reason}`),
}));
