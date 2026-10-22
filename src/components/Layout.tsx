import { NavLink, useNavigate } from 'react-router-dom';
import { Activity, Bell, Building2, ChartNoAxesCombined, ClipboardList, LayoutDashboard, LogOut, Map, Menu, Settings, ShieldCheck, Users, X } from 'lucide-react';
import { useState } from 'react';
import { useAppStore } from '../store';
import type { Role } from '../types';

const links = [
  {to:'/admin/dashboard',label:'Overview',icon:LayoutDashboard},
  {to:'/admin/issues',label:'Issue queue',icon:ClipboardList},
  {to:'/admin/campus-map',label:'3D campus',icon:Map},
  {to:'/admin/analytics',label:'Analytics',icon:ChartNoAxesCombined},
  {to:'/admin/departments',label:'Departments',icon:Users},
  {to:'/admin/audit-log',label:'Audit log',icon:ShieldCheck},
  {to:'/settings',label:'Settings',icon:Settings}
];
export default function Layout({children,title,subtitle}:{children:React.ReactNode;title:string;subtitle?:string}) {
  const [mobileOpen,setMobileOpen]=useState(false);
  const role=useAppStore(s=>s.role); const setRole=useAppStore(s=>s.setRole); const notices=useAppStore(s=>s.notices);
  const navigate=useNavigate();
  const student=role==='Student';
  const navLinks=student?[{to:'/student/dashboard',label:'My dashboard',icon:LayoutDashboard},{to:'/student/report',label:'Report an issue',icon:ClipboardList},{to:'/student/issues',label:'My reports',icon:Activity},{to:'/admin/campus-map',label:'Explore campus',icon:Map},{to:'/settings',label:'Settings',icon:Settings}]:links;
  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen?'open':''}`}>
      <div className="brand"><div className="brand-mark"><Building2 size={20}/></div><div><strong>CampusAlly</strong><span>MANIT BHOPAL</span></div><button className="mobile-close" onClick={()=>setMobileOpen(false)}><X size={18}/></button></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav>{navLinks.map(({to,label,icon:Icon})=><NavLink key={to} to={to} onClick={()=>setMobileOpen(false)} className={({isActive})=>`nav-item ${isActive?'active':''}`}><Icon size={17}/><span>{label}</span>{label==='Issue queue'&&<b>{useAppStore.getState().issues.filter(i=>i.status!=='Resolved').length}</b>}</NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="system-status"><span className="live-dot"></span><div><strong>System operational</strong><small>Demo environment</small></div></div><div className="sidebar-foot">CAMPUS INTELLIGENCE SYSTEM<br/><span>v1.0 · PROTOTYPE</span></div></div>
    </aside>
    {mobileOpen&&<div className="scrim" onClick={()=>setMobileOpen(false)} />}
    <main className="main-area">
      <header className="topbar"><button className="icon-button mobile-menu" onClick={()=>setMobileOpen(true)}><Menu size={19}/></button><div className="breadcrumb">CampusAlly <span>/</span> MANIT Bhopal</div><div className="top-actions"><span className="demo-pill">DEMO MODE</span><button className="icon-button" title="Notifications" onClick={()=>navigate('/settings')}><Bell size={18}/>{notices.some(n=>!n.read)&&<i/>}</button><div className="avatar">{role==='Student'?'ST':role==='Administrator'?'AD':role==='Warden'?'WD':role==='Super Admin'?'SA':'DS'}</div><select className="role-select" value={role} onChange={e=>{setRole(e.target.value as Role);navigate(e.target.value==='Student'?'/student/dashboard':'/admin/dashboard')}} aria-label="Switch demo role">{(['Student','Warden','Administrator','Department Staff','Super Admin'] as Role[]).map(r=><option key={r}>{r}</option>)}</select></div></header>
      <section className="page-content"><div className="page-heading"><div><div className="eyebrow"><span className="live-dot"/>{student?'STUDENT PORTAL':'CAMPUS INTELLIGENCE SYSTEM'}</div><h1>{title}</h1>{subtitle&&<p>{subtitle}</p>}</div>{student&&<button className="primary-button" onClick={()=>navigate('/student/report')}>＋ Report issue</button>}</div>{children}</section>
    </main>
  </div>;
}