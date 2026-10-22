import { create } from 'zustand';
import type { Issue, IssueStatus, Notice, Role, Department } from './types';
import { seedIssues } from './data';

const read = <T,>(key: string, fallback: T): T => {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) as T : fallback; } catch { return fallback; }
};
const persist = (key: string, value: unknown) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* storage may be unavailable */ } };
const scoreIssue = (safety:number,severity:number,impact:number,waiting:number,related:number) =>
  Math.round(.30*safety + .25*severity + .20*impact + .15*waiting + .10*related);

interface Audit { id:string; at:string; actor:string; action:string; issueId:string; detail:string }
interface AppState {
  issues: Issue[]; role: Role; notices: Notice[]; audit: Audit[];
  setRole: (role:Role)=>void; addIssue:(input:{title:string;description:string;category:Department;location:string;evidence?:string})=>Issue;
  updateStatus:(id:string,status:IssueStatus,note:string)=>void;
  assignIssue:(id:string,department:string,staff:string)=>void;
  confirmDuplicate:(id:string,parentId:string)=>void;
  addNotice:(text:string,issueId?:string)=>void; markNoticeRead:(id:string)=>void; reopenIssue:(id:string,reason:string)=>void; resetDemo:()=>void;
}
const initialIssues = read<Issue[]>('ca-issues', seedIssues);
export const useAppStore = create<AppState>((set,get)=>({
  issues: initialIssues,
  role: read<Role>('ca-role','Administrator'),
  notices: read<Notice[]>('ca-notices', [{id:'n1',text:'CampusAlly demo workspace is ready.',at:new Date().toISOString(),read:false}]),
  audit: read<Audit[]>('ca-audit', []),
  setRole: role => { persist('ca-role',role); set({role}); },
  addNotice: (text,issueId) => set(state => { const notices=[{id:crypto.randomUUID(),text,at:new Date().toISOString(),read:false,issueId},...state.notices]; persist('ca-notices',notices); return {notices}; }),
  markNoticeRead: id => set(state => { const notices=state.notices.map(n=>n.id===id?{...n,read:true}:n); persist('ca-notices',notices); return {notices}; }),
  addIssue: input => {
    const now=new Date();
    const id=`MNT-${String(now.getFullYear()).slice(2)}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}${String(now.getHours()).padStart(2,'0')}${String(now.getMinutes()).padStart(2,'0')}-${Math.random().toString(36).slice(2,6).toUpperCase()}`;
    const text=(input.title+' '+input.description).toLowerCase();
    const category=input.category;
    const safety=/electric|spark|fire|leak|slippery|exposed wire|unsafe/.test(text)?80:25;
    const severity=/continuous|large|broken|urgent|danger|fire/.test(text)?75:50;
    const impact=55, waiting=10, related=10;
    const score=scoreIssue(safety,severity,impact,waiting,related);
    const priority=score>=80?'Critical':score>=65?'High':score>=45?'Medium':'Low';
    const issue:Issue={id,title:input.title,description:input.description,category,location:input.location,priority,score,safety,severity,impact,waiting,related,confidence:.82,status:'Submitted',createdAt:now.toISOString(),assignedTo:'Unassigned',department:category,updates:[{at:now.toISOString(),status:'Submitted',note:'Report submitted by student.'}],createdBy:'Current Demo Student',slaHours:priority==='Critical'?8:priority==='High'?24:48,evidence:input.evidence};
    set(state=>{const issues=[issue,...state.issues];persist('ca-issues',issues); const audit=[{id:crypto.randomUUID(),at:now.toISOString(),actor:'Current Demo Student',action:'Issue submitted',issueId:id,detail:'New complaint created.'},...state.audit];persist('ca-audit',audit);return {issues,audit};});
    get().addNotice(`Complaint ${id} was submitted successfully.`,id);
    return issue;
  },
  updateStatus: (id,status,note) => set(state=>{
    const now=new Date().toISOString();
    const issues=state.issues.map(i=>i.id===id?{...i,status,updates:[...i.updates,{at:now,status,note}]}:i);persist('ca-issues',issues);
    const audit=[{id:crypto.randomUUID(),at:now,actor:get().role,action:'Status updated',issueId:id,detail:`${status}: ${note}`},...state.audit];persist('ca-audit',audit);
    return {issues,audit};
  }),
  assignIssue:(id,department,staff)=>set(state=>{
    const now=new Date().toISOString();
    const issues=state.issues.map(i=>i.id===id?{...i,department,assignedTo:staff,status:'Assigned',updates:[...i.updates,{at:now,status:'Assigned',note:`Assigned to ${staff} (${department}).`}]}:i);persist('ca-issues',issues);
    const audit=[{id:crypto.randomUUID(),at:now,actor:get().role,action:'Issue assigned',issueId:id,detail:`${department} / ${staff}`},...state.audit];persist('ca-audit',audit);
    const issue=issues.find(i=>i.id===id); if(issue)get().addNotice(`Your issue ${id} has been assigned to ${staff}.`,id);
    return {issues,audit};
  }),
  confirmDuplicate:(id,parentId)=>set(state=>{
    const issues=state.issues.map(i=>i.id===id?{...i,duplicateOf:parentId}:i);persist('ca-issues',issues);
    const audit=[{id:crypto.randomUUID(),at:new Date().toISOString(),actor:get().role,action:'Duplicate linked',issueId:id,detail:`Linked to ${parentId}`} ,...state.audit];persist('ca-audit',audit);return {issues,audit};
  }),
  reopenIssue:(id,reason)=>get().updateStatus(id,'Reopened',`Student reopened issue: ${reason}`),
  resetDemo:()=>{persist('ca-issues',seedIssues);persist('ca-audit',[]);persist('ca-notices',[]);set({issues:seedIssues,audit:[],notices:[]});}
}));