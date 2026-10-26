import { useEffect, useState } from 'react';
import { ArrowRight, Check, Loader2, RefreshCw } from 'lucide-react';

type Job = {id:string;prompt:{name:string};status:string;message:string;job_id?:string;phase?:string;asset_id?:string};
type Config = {ssh_configured:boolean;blender_configured:boolean;image_provider:string};
async function api<T>(path:string, body?:unknown):Promise<T>{
  const response=await fetch('/api/studio/assets/automation/'+path,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const value=await response.json();
  if(!response.ok)throw new Error(typeof value.detail==='string'?value.detail:'The asset action failed.');
  return value as T;
}
const defaults='Compact two-seat couch with charcoal woven upholstery, two seat cushions, straight padded arms and four short dark wooden legs. No loose pillows.';

export function AssetAutomationPanel({onAsset}:{onAsset:(id:string)=>void}){
  const [config,setConfig]=useState<Config|null>(null);
  const [jobs,setJobs]=useState<Job[]>([]);
  const [family,setFamily]=useState('couch');
  const [name,setName]=useState('Charcoal two-seat couch');
  const [description,setDescription]=useState(defaults);
  const [dimensions,setDimensions]=useState([1.8,.85,.85]);
  const [seed,setSeed]=useState(42);
  const [busy,setBusy]=useState('');
  const [error,setError]=useState('');
  const [notice,setNotice]=useState('');
  useEffect(()=>{
    let alive=true;
    const refresh=()=>void Promise.all([api<Config>('config'),api<Job[]>('jobs')]).then(([c,j])=>{if(alive){setConfig(c);setJobs(j);}}).catch(()=>{if(alive)setError('Could not load asset automation. Check the local app.');});
    refresh();const timer=setInterval(refresh,5000);
    return()=>{alive=false;clearInterval(timer);};
  },[]);
  const active=jobs.some(j=>['queued','connecting','submitting','remote','importing','preparing','connection_lost','interrupted','submission_unknown'].includes(j.status));
  const valid=name.trim().length>=3&&description.trim().length>=10&&dimensions.every(n=>Number.isFinite(n)&&n>=.1&&n<=4)&&Number.isInteger(seed)&&seed>=0&&seed<=2147483647;
  async function action(label:string,fn:()=>Promise<void>){
    setBusy(label);setError('');setNotice('');
    try{await fn();setJobs(await api<Job[]>('jobs'));}catch(e){setError(e instanceof Error?e.message:'Asset action failed.');}finally{setBusy('');}
  }
  return <section className="al-automation" aria-label="Generate furniture from a description">
    <div className="sw-results-title"><div><span className="sw-section-label">FROM DESCRIPTION TO ASSET</span><h2>Describe it. Build it.</h2></div><span>{config?.ssh_configured?'ARC configured':'ARC setup needed'}</span></div>
    <p>A reference image is generated on ARC, then turned into a textured model. Blender cleans a copy, creates convex collision pieces and saves an Unreal import package.</p>
    {!config?.ssh_configured&&<p className="sw-notice">One-time setup: configure your verified ARC SSH connection in the backend and update the ARC checkout. Keep VPN connected off campus. Follow docs/asset-automation-runbook.md; never enter a password or private key here.</p>}
    {config&&!config.blender_configured&&<p className="sw-notice">Set the local Blender executable in Connections before starting. Preparation uses a bounded MCP worker in the background.</p>}
    <div className="al-fields"><label>Design family<select value={family} onChange={e=>setFamily(e.target.value)}><option value="couch">Couch</option><option value="chair">Chair</option></select></label><label>Design name<input value={name} maxLength={80} onChange={e=>setName(e.target.value)}/></label></div>
    <label>What should it look like?<textarea value={description} maxLength={2000} onChange={e=>setDescription(e.target.value)}/></label>
    <div className="al-fields al-measures">{['Width','Depth','Height'].map((label,i)=><label key={label}>{label} target (m)<input type="number" min={.1} max={4} step={.01} value={dimensions[i]} onChange={e=>setDimensions(v=>v.map((n,k)=>k===i?Number(e.target.value):n))}/></label>)}<label>Generation seed<input type="number" min={0} max={2147483647} value={seed} onChange={e=>setSeed(Number(e.target.value))}/></label></div>
    <p className="sw-muted">One design per run. ARC allocation usage applies; first use downloads the pinned SDXL model. Target height is matched uniformly; generated proportions and actual size are reported.</p>
    <div className="sw-actions"><button className="sw-generate" disabled={!!busy||active||!valid||!config?.ssh_configured||!config?.blender_configured} onClick={()=>void action('generate',async()=>{
      const job=await api<Job>('jobs',{family,name,description,dimensions_m:dimensions,seed});
      setNotice('Saved dispatch '+job.id.slice(0,8)+'. Its recorded status below is the source of progress.');
    })}>{busy==='generate'?<Loader2 size={15} className="sw-spin"/>:<ArrowRight size={15}/>}Generate & prepare</button>
    <button disabled={!!busy||!config?.ssh_configured} onClick={()=>void action('check',async()=>{const result=await api<{message:string}>('check',{});setNotice(result.message);})}>{busy==='check'?<Loader2 size={14} className="sw-spin"/>:<Check size={14}/>}Check ARC connection</button></div>
    {error&&<p role="alert" className="sw-error">{error}</p>}{notice&&<p role="status" className="sw-notice">{notice}</p>}
    <div className="al-dispatches">{jobs.slice(0,10).map(job=><article key={job.id} className="al-dispatch">
      <div><strong>{job.prompt.name}</strong><small>{job.id.slice(0,8)}{job.job_id?' Â· Slurm '+job.job_id:''}</small></div>
      <span className="sw-section-label">{job.status.replaceAll('_',' ')}</span><p role="status">{job.message}</p>
      <div className="sw-actions">{['connection_lost','interrupted','submission_unknown'].includes(job.status)&&<button disabled={!!busy} onClick={()=>void action('resume',async()=>{await api('jobs/'+job.id+'/resume',{});})}><RefreshCw size={14}/>Reconnect / resume same job</button>}
      {job.asset_id&&<button onClick={()=>{if(job.asset_id)onAsset(job.asset_id);}}>Open generated design <ArrowRight size={14}/></button>}</div>
    </article>)}</div>
    <p className="sw-muted">Automatic preparation produces a review candidate. Inspect shape, materials, scale and collision fit before Unreal import and collision cooking. New designs are not silently added to the existing chair-only room demos.</p>
  </section>;
}
