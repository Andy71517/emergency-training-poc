import { useCallback, useEffect, useState } from "react";
import { ArrowDownToLine, ArrowRight, Box, Check, ChevronRight, Circle, Command, Layers3, Loader2, Plus, Radio, Sparkles, Terminal, X } from "lucide-react";
import "./spatial-workbench.css";

type Scene = { scene_id: string; objects: unknown[]; room: {width_m:number;depth_m:number}; designated_aisle: {condition:string} };
type Job = {id:string;prompt:string;count:number;seed:number;model:string;status:string;created_at:string;error:string|null;plan: {title:string;assumptions:string[]}|null;scenes:Scene[]};
type Config = {configured:boolean;model:string};
const initialPrompt = "Create classroom-style room layouts using the reviewed wooden chair asset. Include a visible exit and a designated aisle. Keep most layouts clear and obstruct the aisle in the final layout.";
const labels:Record<string,string> = {queued:"Queued",planning:"Interpreting prompt",building:"Building layouts",review_ready:"Ready for review",failed:"Needs attention",interrupted:"Interrupted"};
const active = (j:Job) => ["queued","planning","building"].includes(j.status);
const fileUrl = (job:Job,name:string) => `/api/studio/jobs/${job.id}/files/${name}`;

export function SpatialWorkbench({onLegacy}:{onLegacy:()=>void}) {
  const [config,setConfig]=useState<Config|null>(null);
  const [jobs,setJobs]=useState<Job[]>([]);
  const [selected,setSelected]=useState<string|null>(null);
  const [prompt,setPrompt]=useState(initialPrompt);
  const [count,setCount]=useState(3);
  const [seed,setSeed]=useState(20261018);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [expanded,setExpanded]=useState<Scene|null>(null);
  const job=jobs.find(j=>j.id===selected);
  const refresh=useCallback(async()=>{
    const [c,j]=await Promise.all([fetch('/api/studio/config'),fetch('/api/studio/jobs')]);
    if(!c.ok||!j.ok) throw new Error('Cannot reach the local backend. Start it and refresh.');
    setConfig(await c.json() as Config);
    setJobs(await j.json() as Job[]);
  },[]);
  useEffect(()=>{
    let mounted=true;
    const tick=()=>void refresh().catch(e=>{if(mounted)setError(String(e.message));});
    tick(); const timer=setInterval(tick,2500);
    return()=>{mounted=false;clearInterval(timer);};
  },[refresh]);
  async function generate(){
    setBusy(true);setError('');setExpanded(null);
    try{
      const response=await fetch('/api/studio/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,count,seed})});
      const payload=await response.json();
      if(!response.ok) throw new Error(typeof payload.detail==='string'?payload.detail:'Check the prompt, batch size and seed.');
      setSelected((payload as Job).id);await refresh();
    }catch(e){setError(e instanceof Error?e.message:'Request failed.');}finally{setBusy(false);}
  }
  useEffect(()=>{
    if(!expanded) return;
    const close=(event:KeyboardEvent)=>{if(event.key==='Escape')setExpanded(null);};
    window.addEventListener('keydown',close);
    return()=>window.removeEventListener('keydown',close);
  },[expanded]);
  const ready=jobs.filter(j=>j.status==='review_ready').length;
  return <div className="spatial-workbench">
    <aside className="sw-sidebar">
      <a className="sw-brand" href="#"><span className="sw-brand-icon"><Layers3 size={21}/></span><span>FIELDWORK<small>SCENARIO STUDIO</small></span></a>
      <div className="sw-workspace-label">PERSONAL WORKSPACE <span>POC</span></div>
      <button className="sw-nav sw-nav-active" onClick={()=>setSelected(null)}><Command size={17}/> Create scenario <ChevronRight size={14}/></button>
      <button className="sw-new" onClick={()=>{setSelected(null);setPrompt('');}}><Plus size={15}/> New prompt</button>
      <div className="sw-section-label">RECENT BATCHES <span>{jobs.length.toString().padStart(2,'0')}</span></div>
      <div className="sw-history">{jobs.length===0?<p>Your first batch starts here.<br/>Describe a space to begin.</p>:jobs.map(j=><button key={j.id} className={`sw-job ${selected===j.id?'selected':''}`} onClick={()=>{setSelected(j.id);setExpanded(null);}}><span className={`sw-job-dot ${j.status}`}/><span>{j.plan?.title||j.prompt.slice(0,30)}<small>{j.count} layouts · {labels[j.status]||j.status}</small></span></button>)}</div>
      <div className="sw-sidebar-bottom"><button onClick={onLegacy}><Terminal size={15}/> Legacy POC tools <ArrowRight size={14}/></button><div className="sw-user"><span>A</span><div>Andy’s workspace<small>Local · single user</small></div></div></div>
    </aside>
    <div className="sw-body">
      <header className="sw-topbar"><span>Workspace <ChevronRight size={13}/> <strong>Scenario generation</strong></span><span className="sw-connection"><i className={config?.configured?'online':''}/>{config?.configured?'ARC configured':config?'ARC key needed':'Connecting'}</span></header>
      <main className="sw-main">
        <div className="sw-eyebrow"><Radio size={14}/> FROM LANGUAGE TO ENVIRONMENT <span>EARLY ACCESS / 01</span></div>
        <div className="sw-heading"><div><h1>Make room for<br/><em>what happens next.</em></h1><p>Describe a space. Explore its possibilities.<br/>Build reproducible scenarios with VT ARC.</p></div><div className="sw-coordinate"><Box size={38} strokeWidth={1}/><span>SPACE / CONDITIONS / VARIATIONS</span><small>PLANNING → REVIEW</small></div></div>
        <section className="sw-composer">
          <div className="sw-composer-head"><span><Sparkles size={16}/> SCENARIO BRIEF</span><span>{config?.model||'ARC hosted model'}</span></div>
          <label className="sw-sr" htmlFor="scenario-prompt">Describe the scenario</label>
          <textarea id="scenario-prompt" value={prompt} onChange={e=>setPrompt(e.target.value)} maxLength={8000} placeholder="An eight-metre classroom. Twelve wooden chairs. One clear way out…"/>
          <div className="sw-composer-footer"><div className="sw-controls"><label>Layouts <input aria-label="Number of layouts" type="number" min={1} max={30} value={count} onChange={e=>setCount(Number(e.target.value))}/></label><span className="sw-control-divider"/><label>Seed <input className="sw-seed" aria-label="Reproducibility seed" type="number" min={0} max={2147483647} value={seed} onChange={e=>setSeed(Number(e.target.value))}/></label></div><button className="sw-generate" disabled={busy||!config?.configured||prompt.trim().length<10||!Number.isInteger(count)||count<1||count>30||!Number.isInteger(seed)||seed<0||seed>2147483647} onClick={()=>void generate()}>{busy?<Loader2 size={16} className="sw-spin"/>:<Sparkles size={16}/>} Generate batch <ArrowRight size={17}/></button></div>
        </section>
        <div className="sw-scope"><span><Check size={13}/> Reviewed wooden chair</span><span><Check size={13}/> Rectangular rooms + one exit</span><span><Check size={13}/> Seeded layouts</span><small>New assets, smoke and agents are not connected yet.</small></div>
        {!config?.configured&&config&&<div className="sw-notice">Connect ARC by setting ARC_LLM_API_KEY in backend/.env. Your key stays on the backend; never enter it in a prompt.</div>}
        {error&&<div role="alert" className="sw-error">{error}<button aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}
        <section className="sw-results">
          <div className="sw-results-title"><div><span className="sw-section-label">OUTPUT / REVIEW</span><h2>{job?.plan?.title||'Your next environment'}</h2></div><span>{job?labels[job.status]:`${ready} batches ready`}</span></div>
          {job?<>
            <div className="sw-pipeline">{[['01','Plan & layouts',job.status==='review_ready'?'complete':active(job)?'running':'attention'],['02','Blender review','Not connected'],['03','Unreal simulation','Not connected']].map(([n,title,status])=><div key={n}><span>{n}</span><strong>{title}</strong><small>{status==='complete'?<Check size={13}/>:status==='running'?<Loader2 size={13} className="sw-spin"/>:<Circle size={10}/>} {status}</small></div>)}</div>
            {job.error&&<div className="sw-error" role="alert">{job.error}</div>}
            {active(job)&&<div className="sw-loading"><Loader2 className="sw-spin"/><h3>{labels[job.status]}</h3><p>ARC is processing your request. You can leave this page;<br/>the job is saved by the local backend.</p></div>}
            {job.status==='review_ready'&&<><div className="sw-gallery">{job.scenes.map((s,i)=><button className="sw-scene-card" key={s.scene_id} onClick={()=>setExpanded(s)}><div className="sw-card-image"><img src={fileUrl(job,s.scene_id+'.svg')} alt={`Top-down ${s.scene_id}, ${s.designated_aisle.condition} designated aisle`}/><span>{String(i+1).padStart(2,'0')}</span></div><div className="sw-card-caption"><div><strong>{s.scene_id.replace('_',' ')}</strong><small>{s.room.width_m} × {s.room.depth_m} m · {s.objects.length} chairs</small></div><span className={s.designated_aisle.condition==='clear'?'clear':'obstructed'}>{s.designated_aisle.condition}</span></div></button>)}</div><div className="sw-result-footer"><p>Geometric aisle checks only. Review required; evacuation behavior is not validated.</p><a href={fileUrl(job,'plan.json')} download><ArrowDownToLine size={14}/> Plan JSON</a><a href={fileUrl(job,'manifest.json')} download><ArrowDownToLine size={14}/> Manifest</a></div><details className="sw-assumptions"><summary>Plan assumptions & original request</summary><p>{job.prompt}</p>{job.plan?.assumptions.map((a,i)=><p key={i}>{a}</p>)}<small>Seed {job.seed} · {job.model} · {new Date(job.created_at).toLocaleString()}</small></details></>}
          </>:<div className="sw-empty"><div className="sw-empty-grid"><Box size={38} strokeWidth={1}/></div><h3>A possibility, not a preset.</h3><p>Your generated room layouts will appear here.<br/>Start with the brief above, or write your own.</p><span>01 DESCRIBE <ChevronRight size={11}/> 02 GENERATE <ChevronRight size={11}/> 03 REVIEW</span></div>}
        </section>
        <footer className="sw-footer"><span>FIELDWORK / EMERGENCY TRAINING POC</span><span>VT ARC → BLENDER → UNREAL <i/> BUILD IN PROGRESS</span></footer>
      </main>
    </div>
    {expanded&&job&&<div className="sw-modal" role="dialog" aria-modal="true" aria-label={expanded.scene_id} onClick={()=>setExpanded(null)}><div onClick={e=>e.stopPropagation()}><button autoFocus aria-label="Close preview" onClick={()=>setExpanded(null)}><X/></button><h2>{expanded.scene_id} / {expanded.designated_aisle.condition}</h2><img src={fileUrl(job,expanded.scene_id+'.svg')} alt="Expanded room layout"/><a href={fileUrl(job,expanded.scene_id+'.json')} download>Download scene specification <ArrowDownToLine size={14}/></a></div></div>}
  </div>;
}
