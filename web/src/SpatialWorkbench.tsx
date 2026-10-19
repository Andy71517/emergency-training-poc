import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowDownToLine, ArrowRight, Box, Check, ChevronRight, Command, Layers3, Loader2, Plus, Radio, RefreshCw, Settings2, Sparkles, Terminal, Upload, X } from 'lucide-react';
import './spatial-workbench.css';
import { RunPlayback, type VideoStage } from './RunPlayback';

type Scene = { scene_id:string; objects:unknown[]; room:{width_m:number;depth_m:number}; designated_aisle:{condition:string} };
type Stage = {status:string;message:string;run?:string;maps?:string[];room_count?:number;maximum_endpoint_displacement_m?:number};
type Job = {id:string;prompt:string;count:number;seed:number;model:string;status:string;created_at:string;error:string|null;plan:{title:string;assumptions:string[]}|null;scenes:Scene[];pipeline?:{blender?:Stage;unreal?:Stage;simulation?:Stage;video?:VideoStage};replay_of?:string};
type Config = {configured:boolean;model:string;blender_ready:boolean;blender_executable_set:boolean;chair_bound:boolean;asset_label:string;requirements:string[];video_available:boolean;engine:{connected:boolean;busy:boolean;project?:string;version?:string;capabilities?:string[];activity?:{job_id:string;action:string;room:number;total:number}|null}};
const initialPrompt='Create classroom-style room layouts using the reviewed wooden chair asset. Include a visible exit and a designated aisle. Keep most layouts clear and obstruct the aisle in the final layout.';
const labels:Record<string,string>={queued:'Queued',planning:'Interpreting prompt',building:'Building layouts',review_ready:'Ready for review',failed:'Needs attention',interrupted:'Interrupted',complete:'Complete',running:'Running',not_started:'Ready to start',assembly_reported:'Assembly reported',playback_reported:'Playback reported'};
const active=(j:Job)=>['queued','planning','building'].includes(j.status);
const fileUrl=(job:Job,name:string)=>`/api/studio/jobs/${job.id}/files/${name}`;
const blenderUrl=(job:Job,name:string)=>`/api/studio/jobs/${job.id}/blender-files/${name}`;
async function request<T>(url:string,body?:unknown):Promise<T>{
  const response=await fetch(url,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const payload=await response.json();
  if(!response.ok)throw new Error(typeof payload.detail==='string'?payload.detail:'Request failed. Check your inputs and try again.');
  return payload as T;
}

export function SpatialWorkbench({onLegacy}:{onLegacy:()=>void}){
  const [config,setConfig]=useState<Config|null>(null);
  const [jobs,setJobs]=useState<Job[]>([]);
  const [selected,setSelected]=useState<string|null>(null);
  const [prompt,setPrompt]=useState(initialPrompt);
  const [count,setCount]=useState(3);
  const [seed,setSeed]=useState(20261018);
  const [busy,setBusy]=useState('');
  const [error,setError]=useState('');
  const [notice,setNotice]=useState('');
  const [expanded,setExpanded]=useState<Scene|null>(null);
  const [connections,setConnections]=useState(false);
  const [stage,setStage]=useState<'plan'|'blender'|'unreal'>('plan');
  const input=useRef<HTMLTextAreaElement>(null);
  const reportInput=useRef<HTMLInputElement>(null);
  const dialogRef=useRef<HTMLDivElement>(null);
  const job=jobs.find(j=>j.id===selected);
  const refresh=useCallback(async()=>{
    const [c,j]=await Promise.all([request<Config>('/api/studio/config'),request<Job[]>('/api/studio/jobs')]);
    setConfig(c);setJobs(j);
  },[]);
  useEffect(()=>{
    let alive=true;
    const tick=()=>void refresh().catch(()=>{if(alive)setError('Cannot reach the local backend. Start it, then refresh the connection.');});
    tick();const timer=setInterval(tick,4000);return()=>{alive=false;clearInterval(timer);};
  },[refresh]);
  useEffect(()=>{
    if(!expanded&&!connections)return;
    const previous=document.activeElement as HTMLElement|null;
    const handler=(event:KeyboardEvent)=>{
      if(event.key==='Escape'){setExpanded(null);setConnections(false);}
      if(event.key==='Tab'){
        const nodes=dialogRef.current?.querySelectorAll<HTMLElement>('button,a[href],input');
        if(!nodes?.length)return;
        const first=nodes[0],last=nodes[nodes.length-1];
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
      }
    };
    window.addEventListener('keydown',handler);return()=>{window.removeEventListener('keydown',handler);previous?.focus();};
  },[expanded,connections]);
  async function act(name:string,operation:()=>Promise<void>){
    setBusy(name);setError('');setNotice('');
    try{await operation();await refresh();}catch(e){setError(e instanceof Error?e.message:'Request failed.');}finally{setBusy('');}
  }
  const choose=(j:Job)=>{setSelected(j.id);setExpanded(null);setStage('plan');setNotice('');};
  const edit=(j?:Job)=>{setSelected(null);setExpanded(null);setStage('plan');if(j){setPrompt(j.prompt);setCount(j.count);setSeed(j.seed);}requestAnimationFrame(()=>input.current?.focus());};
  const generate=()=>act('generate',async()=>{const j=await request<Job>('/api/studio/jobs',{prompt,count,seed});choose(j);});
  const check=()=>act('connection',async()=>{const result=await request<{message:string}>('/api/studio/connection-check',{});setNotice(result.message);});
  const ready=jobs.filter(j=>j.status==='review_ready').length;
  const valid=prompt.trim().length>=10&&Number.isInteger(count)&&count>=1&&count<=30&&Number.isInteger(seed)&&seed>=0&&seed<=2147483647;
  const blender=job?.pipeline?.blender;
  const unreal=job?.pipeline?.unreal;
  const simulation=job?.pipeline?.simulation;
  const video=job?.pipeline?.video;
  const encoding=!!video&&['queued','running'].includes(video.status);
  const canRecord=!!config?.engine.capabilities?.includes('record');
  const activity=config?.engine.activity?.job_id===job?.id?config?.engine.activity:null;
  const engineWorking=[unreal,simulation].some(s=>s&&['queued','running'].includes(s.status));
  const isWorking=blender&&['queued','running'].includes(blender.status);
  const progress=job?active(job)?'Planning':engineWorking?'Simulating / assembling':encoding?'Preparing playback':video?.clips?.length?'Ready to watch':blender?.status==='running'?'Building rooms':job.status==='review_ready'?'Layouts ready':labels[job.status]:'';
  async function importReport(file:File){
    if(!job)return;
    if(file.size>2_000_000){setError('Choose a report smaller than 2 MB.');return;}
    await act('report',async()=>{await request(`/api/studio/jobs/${job.id}/unreal-report`,JSON.parse(await file.text()));setNotice('Matching Unreal assembly report imported.');});
  }
  return <div className="spatial-workbench">
    <aside className="sw-sidebar">
      <button className="sw-brand" onClick={()=>edit()} aria-label="FIELDWORK home"><span className="sw-brand-icon"><Layers3 size={21}/></span><span>FIELDWORK<small>SCENARIO STUDIO</small></span></button>
      <div className="sw-workspace-label">PERSONAL WORKSPACE <span>POC</span></div>
      <button className="sw-nav sw-nav-active" onClick={()=>edit()} title="Create scenario"><Command size={17}/> Create scenario <ChevronRight size={14}/></button>
      <button className="sw-new" onClick={()=>{edit();setPrompt('');}}><Plus size={15}/> New prompt</button>
      <div className="sw-section-label">RECENT BATCHES <span>{jobs.length.toString().padStart(2,'0')}</span></div>
      <div className="sw-history">{jobs.length===0?<p>Your first batch starts here.<br/>Describe a space to begin.</p>:jobs.map(j=><button key={j.id} className={`sw-job ${selected===j.id?'selected':''}`} onClick={()=>choose(j)} title={j.plan?.title||j.prompt}><span className={`sw-job-dot ${j.status}`}/><span>{j.plan?.title||j.prompt.slice(0,30)}<small>{j.count} layouts · {labels[j.status]||j.status}</small></span></button>)}</div>
      <div className="sw-sidebar-bottom"><button onClick={()=>setConnections(true)}><Settings2 size={15}/> Connections <ChevronRight size={14}/></button><button onClick={onLegacy}><Terminal size={15}/> Legacy POC tools <ArrowRight size={14}/></button><div className="sw-user"><span>A</span><div>Andy’s workspace<small>Local · single user</small></div></div></div>
    </aside>
    <div className="sw-body">
      <header className="sw-topbar"><span>Workspace <ChevronRight size={13}/><strong>Scenario generation</strong></span><button className="sw-connection" onClick={()=>setConnections(true)}><i className={config?.configured?'online':''}/>{config?.configured?'ARC key configured':config?'Connect ARC':'Connecting'}<Settings2 size={13}/></button></header>
      <main className="sw-main">
        <div className="sw-eyebrow"><Radio size={14}/> FROM LANGUAGE TO ENVIRONMENT <span>WORKSPACE / 02</span></div>
        <div className="sw-heading"><div><h1>Make room for<br/><em>what happens next.</em></h1><p>Describe a space. Explore its possibilities.<br/>Build reproducible scenarios with VT ARC.</p></div><div className="sw-coordinate"><Box size={38} strokeWidth={1}/><span>SPACE / CONDITIONS / VARIATIONS</span><small>PLAN → ASSEMBLE → INSPECT</small></div></div>
        <section className="sw-composer" aria-label="Scenario brief">
          <div className="sw-composer-head"><span><Sparkles size={16}/> SCENARIO BRIEF</span><span>{config?.model||'ARC hosted model'}</span></div>
          <label className="sw-sr" htmlFor="scenario-prompt">Describe the scenario</label>
          <textarea ref={input} id="scenario-prompt" value={prompt} onChange={e=>setPrompt(e.target.value)} maxLength={8000} placeholder="An eight-metre classroom. Twelve wooden chairs. One clear way out…"/>
          <div className="sw-composer-footer"><div className="sw-controls"><label>Layouts<input aria-label="Number of layouts" type="number" min={1} max={30} value={count} onChange={e=>setCount(Number(e.target.value))}/></label><span className="sw-control-divider"/><label>Seed<input className="sw-seed" aria-label="Reproducibility seed" type="number" min={0} max={2147483647} value={seed} onChange={e=>setSeed(Number(e.target.value))}/></label><span className="sw-char-count">{prompt.length}/8000</span></div><button className="sw-generate" disabled={!!busy||!config?.configured||!valid} onClick={()=>void generate()}>{busy==='generate'?<Loader2 size={16} className="sw-spin"/>:<Sparkles size={16}/>}Generate batch<ArrowRight size={17}/></button></div>
        </section>
        <div className="sw-scope"><span><Check size={13}/> Reviewed wooden chair</span><span><Check size={13}/> Rectangular rooms + one exit</span><span><Check size={13}/> Seeded layouts</span><button onClick={()=>setConnections(true)}>Asset & worker setup <ChevronRight size={12}/></button></div>
        {!config?.configured&&config&&<div className="sw-notice">Add your ARC key to backend/.env, then use Connections to test access. Never put the key in a prompt.</div>}
        {error&&<div role="alert" className="sw-error"><span>{error}</span><button aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}
        {notice&&<div role="status" className="sw-notice">{notice}</div>}
        <section className="sw-results">
          <div className="sw-results-title"><div><span className="sw-section-label">OUTPUT / REVIEW</span><h2>{job?.plan?.title||'Your next environment'}</h2></div><span aria-live="polite">{job?progress:`${ready} batches ready`}</span></div>
          {job?<>
            <div className="sw-pipeline" role="tablist" aria-label="Pipeline stages">{([
              ['plan','01','Plan & layouts',labels[job.status]],['blender','02','Blender assembly',blender?labels[blender.status]||blender.status:config?.blender_ready?'Ready to start':'Setup needed'],['unreal','03','Unreal / Chaos',encoding?'Preparing playback':video?.clips?.length?'Ready to watch':simulation?labels[simulation.status]||simulation.status:unreal?labels[unreal.status]||unreal.status:config?.engine.connected?'Editor connected':'Connect editor']
            ] as const).map(([key,n,title,status])=><button role="tab" aria-selected={stage===key} key={key} onClick={()=>setStage(key)} className={stage===key?'sw-stage-active':''}><span>{n}</span><strong>{title}</strong><small>{status}</small></button>)}</div>
            {stage==='plan'&&<>
              {job.error&&<div className="sw-error" role="alert"><div><strong>Planning stopped</strong><p>{job.error}</p></div></div>}
              {active(job)&&<div className="sw-loading"><Loader2 className="sw-spin"/><h3>{labels[job.status]}</h3><p>Waiting for ARC and saving this batch locally. You can switch batches while it runs.</p></div>}
              {!active(job)&&<div className="sw-actions"><button onClick={()=>edit(job)}>Edit this brief</button>{job.plan&&<button disabled={!!busy} onClick={()=>void act('replay',async()=>{choose(await request<Job>(`/api/studio/jobs/${job.id}/replay`,{seed}));setNotice('Replaying saved plan. No ARC model request was made.');})}><RefreshCw size={14}/> Rebuild with seed {seed}</button>}{job.status==='failed'&&<button disabled={!!busy} onClick={()=>void act('retry',async()=>{choose(await request<Job>('/api/studio/jobs',{prompt:job.prompt,count:job.count,seed:job.seed}));})}>Retry ARC request</button>}<button disabled={!!busy} onClick={()=>void check()}>Test ARC connection</button></div>}
              {job.status==='review_ready'&&<><div className="sw-gallery">{job.scenes.map((s,i)=><button className="sw-scene-card" key={s.scene_id} onClick={()=>setExpanded(s)}><div className="sw-card-image"><img src={fileUrl(job,s.scene_id+'.svg')} alt={`Top-down ${s.scene_id}, ${s.designated_aisle.condition} designated aisle`}/><span>{String(i+1).padStart(2,'0')}</span></div><div className="sw-card-caption"><div><strong>{s.scene_id.replace('_',' ')}</strong><small>{s.room.width_m} × {s.room.depth_m} m · {s.objects.length} chairs</small></div><span className={s.designated_aisle.condition==='clear'?'clear':'obstructed'}>{s.designated_aisle.condition}</span></div></button>)}</div><div className="sw-result-footer"><p>Aisle footprint checks only. Review before simulation.</p><a href={`/api/studio/jobs/${job.id}/bundle/spatial`} download><ArrowDownToLine size={14}/> Whole batch</a><a href={fileUrl(job,'plan.json')} download>Plan JSON</a><a href={fileUrl(job,'manifest.json')} download>Manifest</a></div><details className="sw-assumptions"><summary>Plan assumptions & original request</summary><p>{job.prompt}</p>{job.plan?.assumptions.map((a,i)=><p key={i}>{a}</p>)}<small>Seed {job.seed} · {job.model} · {new Date(job.created_at).toLocaleString()}{job.replay_of?' · Saved-plan replay':''}</small></details></>}
            </>}
            {stage==='blender'&&<div className="sw-worker-panel"><p className="sw-eyebrow">LOCAL APPLICATION WORKER</p><h3>From layouts to a furnished room.</h3><p>Assemble your prepared chair asset into every layout in a new Blender file. The worker preserves the source chair and renders a preview.</p><div className="sw-actions"><button disabled={!!busy||!!isWorking||job.status!=='review_ready'||!config?.blender_ready} onClick={()=>void act('blender',async()=>{await request(`/api/studio/jobs/${job.id}/blender`,{});})}>{isWorking?<Loader2 size={15} className="sw-spin"/>:<Box size={15}/>} {isWorking?'Blender is working':blender?.status==='complete'?'Build a new revision':'Build in Blender'}</button><button onClick={()=>setConnections(true)}>Configure worker</button></div>{!config?.blender_ready&&<p className="sw-muted">Set the Blender executable and prepared chair path in backend/.env first.</p>}{blender&&<p role="status">{blender.message}</p>}{blender?.status==='complete'&&<><a href={blenderUrl(job,'preview.png')} target="_blank" rel="noreferrer" title="Open full render"><img className="sw-render" src={blenderUrl(job,'preview.png')} alt="Rendered Blender room batch. Open full render."/></a><div className="sw-actions"><a href={blenderUrl(job,'rooms.blend')} download><ArrowDownToLine size={14}/> Download rooms.blend</a><a href={blenderUrl(job,'report.json')} download>Assembly report</a><button onClick={()=>setStage('unreal')}>Continue to Unreal <ArrowRight size={14}/></button></div></>}</div>}
            {stage==='unreal'&&<div className="sw-worker-panel"><p className="sw-eyebrow">UNREAL ENGINE 5.8 / CHAOS</p><h3>Build the maps. Observe the physics.</h3><p>Connect the local editor once, then assemble layouts and request ten seconds of Chaos playback per map. Keep Unreal open, stop existing simulation, and save your work first.</p><div className="sw-actions"><button disabled={!!busy||engineWorking||encoding||!!config?.engine.busy||!config?.engine.connected||job.status!=='review_ready'} onClick={()=>void act('engine',async()=>{await request(`/api/studio/jobs/${job.id}/engine/assemble`,{});})}>{engineWorking?<Loader2 size={14} className="sw-spin"/>:<Box size={14}/>}Assemble in Unreal</button><button disabled={!!busy||engineWorking||encoding||!!config?.engine.busy||!config?.engine.connected||!unreal?.maps?.length} onClick={()=>void act('simulate',async()=>{await request(`/api/studio/jobs/${job.id}/engine/simulate`,{});})}><Radio size={14}/>Run Chaos batch</button><button className="sw-record-button" disabled={!!busy||engineWorking||encoding||!config?.engine.connected||!canRecord||!config?.video_available||!unreal?.maps?.length} onClick={()=>void act('record',async()=>{await request(`/api/studio/jobs/${job.id}/engine/record`,{});})}><Sparkles size={14}/>Record movement demo</button><button onClick={()=>setConnections(true)}>Connect editor</button></div>
              <p className="sw-muted">{config?.engine.connected?`Editor connected · ${config.engine.project||'local project'}`:'Editor bridge not detected. Open Connections for the one-time setup.'}</p>{unreal&&<p role="status">{unreal.message}</p>}{simulation&&<p role="status">{activity&&['record','simulate'].includes(activity.action)?`${activity.action==='record'?'Recording':'Simulating'} room ${activity.room} of ${activity.total}…`:simulation.message}</p>}{!config?.video_available&&<p className="sw-muted">Video support needs an update: run the Python install command shown in Connections.</p>}{config?.engine.connected&&!canRecord&&<p className="sw-muted">Reload the editor worker once to enable recording.</p>}
              {blender?.status!=='complete'&&<p className="sw-muted">Blender has not run for this batch. These are spatial drafts; inspect the layouts before assembly.</p>}
              {unreal?.maps&&<div className="sw-engine-evidence"><Check size={17}/><div><strong>Matching assembly report received</strong>{unreal.maps.map(path=><code key={path}>{path}</code>)}</div></div>}
              {simulation?.status==='playback_reported'&&<div className="sw-engine-evidence"><Radio size={17}/><div><strong>{simulation.room_count} maps observed by the editor</strong><p>Largest chair endpoint displacement: {simulation.maximum_endpoint_displacement_m?.toFixed(3)} m. Floor-level chairs may remain still.</p><a href={`/api/studio/jobs/${job.id}/chaos-report`} download>Download Chaos observations</a></div></div>}
              <RunPlayback jobId={job.id} video={video} busy={!!busy||engineWorking||encoding} onRetry={()=>void act('video-retry',async()=>{await request(`/api/studio/jobs/${job.id}/video-retry`,{});})}/>
              <details className="sw-assumptions"><summary>Portable handoff & report import</summary><p>Alternative route: extract the ZIP, open the original chair demo, then Tools → Execute Python Script → assemble_unreal58_rooms.py. Import the matching Saved/EmergencyPOC/room-setup report below.</p><div className="sw-actions">{job.status==='review_ready'&&<a href={`/api/studio/jobs/${job.id}/bundle/unreal`} download><ArrowDownToLine size={14}/>Unreal handoff ZIP</a>}<button disabled={!!busy||job.status!=='review_ready'} onClick={()=>reportInput.current?.click()}><Upload size={14}/>Import assembly report</button><input hidden ref={reportInput} type="file" accept=".json" onChange={e=>{const f=e.target.files?.[0];if(f)void importReport(f);e.target.value='';}}/></div></details>
              <p className="sw-muted">Playback reports measure chair positions in the game world. Collision contacts, evacuation behavior and physical calibration remain unvalidated. The movement demo returns recorded clips; it does not stream the editor live.</p></div>}

          </>:<div className="sw-empty"><div className="sw-empty-grid"><Box size={38} strokeWidth={1}/></div><h3>A possibility, not a preset.</h3><p>Generate a batch, inspect the layouts, build in Blender,<br/>then hand the same specifications to Unreal.</p><button className="sw-text-button" onClick={()=>input.current?.focus()}>Write your brief <ArrowRight size={13}/></button></div>}
        </section>
        <footer className="sw-footer"><span>FIELDWORK / EMERGENCY TRAINING POC</span><button onClick={()=>setConnections(true)}>PIPELINE CONNECTIONS <ChevronRight size={11}/></button></footer>
      </main>
    </div>
    {(expanded||connections)&&<div className="sw-modal" onClick={()=>{setExpanded(null);setConnections(false);}}><div ref={dialogRef} role="dialog" aria-modal="true" aria-label={connections?'Pipeline connections':expanded?.scene_id} onClick={e=>e.stopPropagation()}><button autoFocus className="sw-modal-close" aria-label="Close dialog" onClick={()=>{setExpanded(null);setConnections(false);}}><X/></button>{connections?<>
      <p className="sw-eyebrow">PIPELINE CONNECTIONS</p><h2>One setup. Repeatable batches.</h2><div className="sw-connection-row"><strong>VT ARC planner</strong><span>{config?.configured?'Key configured · not yet a connectivity check':'Key needed'}</span></div><p>Set ARC_LLM_API_KEY and ARC_LLM_MODEL in backend/.env. The key stays on this computer’s backend. Testing makes a small model request.</p><button className="sw-generate" disabled={!!busy||!config?.configured} onClick={()=>void check()}>{busy==='connection'?<Loader2 size={15} className="sw-spin"/>:<Radio size={15}/>}Test ARC connection</button>{notice&&<p role="status" className="sw-notice">{notice}</p>}{error&&<p role="alert" className="sw-error">{error}</p>}
      <div className="sw-connection-row"><strong>Blender 5.1 worker</strong><span>{config?.blender_ready?'Paths ready':'Setup needed'}</span></div><p>Add these two lines to the same backend/.env file, using your real paths. Restarting is not required for path changes.</p><pre>{'BLENDER_EXECUTABLE=C:/Program Files/Blender Foundation/Blender 5.1/blender.exe\nCHAIR_BLEND=C:/your-assets/chair-collision-complete.blend'}</pre><p>Executable: {config?.blender_executable_set?'found':'not found'} · Prepared chair: {config?.chair_bound?'found':'not found'}</p><button className="sw-text-button" onClick={()=>void act('refresh',async()=>{await refresh();setNotice('Configuration refreshed.');})}><RefreshCw size={14}/>Refresh paths</button>
      <div className="sw-connection-row"><strong>Unreal Engine 5.8</strong><span>{config?.engine.connected?'Editor connected':'Bridge not loaded'}</span></div><p>Open your saved original chair demo in Unreal 5.8. Choose Tools → Execute Python Script, then select this checkout’s unreal/scripts/studio_bridge.py. Keep the editor open. The bridge only handles fixed assembly and playback actions from this local checkout.</p><pre>unreal/scripts/studio_bridge.py</pre><p>After an update, execute that same script again while no run is active. Recording support: {canRecord?'worker ready':'reload worker'}. Video encoder: {config?.video_available?'installed':'install needed'}.</p><pre>{'.\\.venv\\Scripts\\python.exe -m pip install -e .'}</pre><p>Save your current level and stop simulation before sending work. First assembly binds the reviewed Display chair asset; later batches reuse that binding during this editor session.</p><div className="sw-connection-row"><strong>Reviewed asset</strong><span>Hunyuan / ARC</span></div><p>{config?.asset_label}. The prepared chair includes 19 collision pieces. Generating additional asset types on ARC and repairing them are not automated by this worker.</p>
    </>:expanded&&job&&<><h2>{expanded.scene_id} / {expanded.designated_aisle.condition}</h2><img src={fileUrl(job,expanded.scene_id+'.svg')} alt="Expanded room layout"/><a href={fileUrl(job,expanded.scene_id+'.json')} download>Download scene specification <ArrowDownToLine size={14}/></a></>}</div></div>}
  </div>;
}
