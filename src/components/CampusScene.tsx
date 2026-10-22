import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html, Float } from '@react-three/drei';
import { Suspense, useState } from 'react';
import type { Issue } from '../types';

const buildings = [
  {name:'Academic Block',position:[-2,0,-1] as [number,number,number],size:[2.1,1.5,1.6] as [number,number,number],color:'#203e5c'},
  {name:'Central Library',position:[1.7,0,-1.6] as [number,number,number],size:[1.5,1.9,1.5] as [number,number,number],color:'#294e6a'},
  {name:'Hostel 1',position:[-3.7,0,2] as [number,number,number],size:[1.2,1.6,1.3] as [number,number,number],color:'#28445b'},
  {name:'Hostel 2',position:[-1.9,0,3.1] as [number,number,number],size:[1.3,1.4,1.2] as [number,number,number],color:'#31516a'},
  {name:'Hostel 3',position:[2.8,0,2.6] as [number,number,number],size:[1.5,1.6,1.4] as [number,number,number],color:'#25445f'},
  {name:'Student Activity Centre',position:[4.2,0,-.8] as [number,number,number],size:[1.6,1.2,1.3] as [number,number,number],color:'#31516a'}
];
const locations:Record<string,[number,number,number]> = {
  'Hostel 3 · Main entrance':[2.8,.5,1.85],
  'Library road · Pole E-12':[0,.1,-.1],
  'Central Library · Floor 2':[1.7,1,-1.6],
  'Academic Block · Canteen':[-2,.7,-1],
  'Academic Block · East pathway':[-.8,.1,-.4],
  'Hostel 2 · Mess':[-1.9,.7,2.6]
};
function Building({b}:{b:typeof buildings[number]}) {
  return <group position={b.position}>
    <mesh position={[0,b.size[1]/2,0]} castShadow><boxGeometry args={b.size}/><meshStandardMaterial color={b.color} roughness={.72}/></mesh>
    <mesh position={[0,b.size[1]+.06,0]}><boxGeometry args={[b.size[0]+.12,.12,b.size[2]+.12]}/><meshStandardMaterial color="#43d9f8" emissive="#0b4558" emissiveIntensity={.35}/></mesh>
    {Array.from({length:Math.max(2,Math.floor(b.size[1]*2))}).map((_,i)=><mesh key={i} position={[0,.35+i*.36,b.size[2]/2+.008]}><boxGeometry args={[b.size[0]*.72,.09,.025]}/><meshStandardMaterial color="#69dff8" emissive="#1b6b84" emissiveIntensity={.6}/></mesh>)}
    <Html position={[0,b.size[1]+.35,0]} center distanceFactor={12}><div className="building-label">{b.name}</div></Html>
  </group>;
}
function Scene({issues,selected,onSelect,selectable}:{issues:Issue[];selected?:string;onSelect?:(location:string)=>void;selectable:boolean}) {
  return <>
    <ambientLight intensity={1.3}/><directionalLight position={[5,9,5]} intensity={2.1} castShadow/>
    <mesh rotation={[-Math.PI/2,0,0]} position={[0,-.08,0]} receiveShadow><planeGeometry args={[18,14]}/><meshStandardMaterial color="#0d1b2a"/></mesh>
    <gridHelper args={[18,18,'#24465b','#142b3d']} position={[0,-.06,0]}/>
    {Array.from({length:5}).map((_,i)=><mesh key={`road${i}`} position={[0,-.045,-4+i*2]} rotation={[-Math.PI/2,0,0]}><planeGeometry args={[16,.34]}/><meshStandardMaterial color="#172838"/></mesh>)}
    {buildings.map(b=><Building key={b.name} b={b}/>)}
    {Array.from({length:18}).map((_,i)=><mesh key={`tree${i}`} position={[-6+(i%6)*2.1,.18,-3+Math.floor(i/6)*3]}><sphereGeometry args={[.22,8,8]}/><meshStandardMaterial color="#1b806f" emissive="#0b3b35" emissiveIntensity={.25}/></mesh>)}
    {issues.filter(i=>i.status!=='Resolved').map((issue,index)=>{
      const pos=locations[issue.location] || [-3+(index%4)*2,.2,-3+Math.floor(index/4)*2];
      const color=issue.priority==='Critical'?'#ff5d73':issue.priority==='High'?'#ffad66':issue.priority==='Medium'?'#ffcf70':'#43d9f8';
      return <group key={issue.id} position={pos} onClick={()=>onSelect?.(issue.location)}>
        <Float speed={1.4} rotationIntensity={0} floatIntensity={.16}>
          <mesh><sphereGeometry args={[selected === issue.location ? .17 : .12,16,16]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={1.8}/></mesh>
          <mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[.25,.018,6,24]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={1}/></mesh>
        </Float>
        <Html distanceFactor={10} position={[0,.45,0]} center><button className="marker-label" onClick={(e)=>{e.stopPropagation();onSelect?.(issue.location)}}>{issue.priority==='Critical'?'!':'•'} {issue.title}</button></Html>
      </group>;
    })}
    {selectable && <Html position={[0,2.8,0]} center><div className="scene-hint">Select a campus area to set the report location</div></Html>}
    <OrbitControls makeDefault enableDamping minDistance={6} maxDistance={22} maxPolarAngle={Math.PI/2.05}/>
  </>;
}
export default function CampusScene({issues,selected,onSelect,selectable=false}:{issues:Issue[];selected?:string;onSelect?:(location:string)=>void;selectable?:boolean}) {
  const [failed,setFailed]=useState(false);
  if(failed)return <div className="scene-fallback">3D view unavailable. Use the searchable location selector instead.</div>;
  return <div className="campus-canvas"><Canvas camera={{position:[9,8,10],fov:43}} dpr={[1,1.5]} onCreated={()=>{}}><Suspense fallback={null}><Scene issues={issues} selected={selected} onSelect={onSelect} selectable={selectable}/></Suspense></Canvas><button className="scene-reset" onClick={()=>window.dispatchEvent(new Event('campus-reset'))}>3D CAMPUS · DRAG TO ORBIT</button></div>;
}