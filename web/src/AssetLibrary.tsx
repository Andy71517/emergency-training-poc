import { Component, Suspense, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Canvas, useFrame, useLoader, useThree } from '@react-three/fiber';
import { Box3, Vector3 } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { ArrowDownToLine, ArrowRight, Box, Check, Loader2, Plus, Upload } from 'lucide-react';
import './asset-library.css';
import { AssetAutomationPanel } from './AssetAutomationPanel';

type Variant = {id:string;family:string;name:string;description:string;dimensions_m:number[];status:string;room_compatible:boolean;blender?:{status:string;message:string;report?:{staged_dimensions_m:number[];collision_mesh_created?:boolean;hull_count?:number}};builtin?:boolean;reused?:boolean};
const names:Record<string,string>={demo_ready:'Ready in room demos',binding_needed:'Set the chair path in Connections',ready_for_arc:'Ready to send to ARC',generated_review_needed:'Generated · Blender review next'};
const reference='/references/charcoal-two-seat-couch.webp';
const initialDesign='Compact two-seat couch with charcoal woven upholstery, two seat cushions, straight padded arms and four short dark wooden legs. No loose pillows.';
async function json<T>(url:string,init?:RequestInit):Promise<T>{const r=await fetch(url,init);const value=await r.json();if(!r.ok)throw new Error(typeof value.detail==='string'?value.detail:'The asset request failed.');return value as T;}
const fileUrl=(a:Variant,n:string)=>`/api/studio/assets/${a.id}/files/${n}`;
async function presetPng():Promise<Blob>{const image=new Image();image.src=reference;await image.decode();const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const context=canvas.getContext('2d');if(!context)throw new Error('Could not read the reference image.');context.drawImage(image,0,0);return new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error('Could not encode the reference image.')),'image/png'));}
function asDataUrl(file:Blob):Promise<string>{return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=()=>reject(new Error('Could not read the image.'));reader.readAsDataURL(file);});}

function CameraControls(){
  const {camera,gl}=useThree();const controls=useRef<OrbitControls|null>(null);
  useEffect(()=>{const c=new OrbitControls(camera,gl.domElement);c.enableDamping=true;c.minDistance=.6;c.maxDistance=6;controls.current=c;return()=>{c.dispose();controls.current=null;};},[camera,gl]);
  useFrame(()=>controls.current?.update());return null;
}
function Model({url}:{url:string}){
  const gltf=useLoader(GLTFLoader,url);
  const {scene,center,scale}=useMemo(()=>{const scene=gltf.scene.clone(true);const bounds=new Box3().setFromObject(scene);const size=bounds.getSize(new Vector3());const center=bounds.getCenter(new Vector3());const scale=1.7/Math.max(size.x,size.y,size.z,.001);return {scene,center,scale};},[gltf]);
  return <group scale={scale}><primitive object={scene} position={[-center.x,-center.y,-center.z]}/></group>;
}
class ModelBoundary extends Component<{children:ReactNode},{failed:boolean}>{
  state={failed:false};static getDerivedStateFromError(){return {failed:true};}
  render(){return this.state.failed?<p role="alert">This model could not be displayed. Download the GLB and inspect it in Blender.</p>:this.props.children;}
}
function Viewer({asset}:{asset:Variant}){return <ModelBoundary key={asset.id}><Suspense fallback={<p>Loading the generated model…</p>}><div className="al-viewer"><Canvas camera={{position:[1.8,1.1,2.2],fov:42}}><color attach="background" args={['#11191b']}/><ambientLight intensity={1.8}/><directionalLight position={[3,5,4]} intensity={3}/><directionalLight position={[-3,1,-2]} intensity={1}/><Model url={fileUrl(asset,'asset.glb')}/><CameraControls/></Canvas></div></Suspense></ModelBoundary>;}

export function AssetLibrary({onBack}:{onBack:()=>void}){
  const [assets,setAssets]=useState<Variant[]>([]);const [selected,setSelected]=useState<string>('');
  const [family,setFamily]=useState('couch');const [name,setName]=useState('Charcoal two-seat couch');const [description,setDescription]=useState(initialDesign);
  const [dimensions,setDimensions]=useState([1.8,.85,.85]);const [seed,setSeed]=useState(42);const [image,setImage]=useState(reference);
  const [busy,setBusy]=useState('');const [error,setError]=useState('');const [notice,setNotice]=useState('');const [creating,setCreating]=useState(false);
  const upload=useRef<HTMLInputElement>(null);const target=useRef<string>('');
  const current=assets.find(a=>a.id===selected);
  const refresh=async()=>setAssets(await json<Variant[]>('/api/studio/assets'));
  useEffect(()=>{let alive=true;const tick=()=>void json<Variant[]>('/api/studio/assets').then(a=>{if(alive)setAssets(a);}).catch(()=>{if(alive)setError('Could not load the asset library. Check the local backend.');});tick();const timer=setInterval(tick,4000);return()=>{alive=false;clearInterval(timer);};},[]);
  async function act(label:string,fn:()=>Promise<void>){setBusy(label);setError('');setNotice('');try{await fn();await refresh();}catch(e){setError(e instanceof Error?e.message:'Asset operation failed.');}finally{setBusy('');}}
  const generated=(a:Variant)=>a.status==='generated_review_needed';
  const changeFamily=(next:string)=>{setFamily(next);setName(next==='couch'?'Charcoal two-seat couch':'Metal folding chair');setDescription(next==='couch'?initialDesign:'Simple metal folding chair with a dark padded seat, a curved metal back and four slim metal legs.');setDimensions(next==='couch'?[1.8,.85,.85]:[.5,.55,.85]);setImage(next==='couch'?reference:'');};
  const valid=name.trim().length>=3&&description.trim().length>=10&&dimensions.every(n=>Number.isFinite(n)&&n>=.1&&n<=4)&&Number.isInteger(seed)&&seed>=0&&seed<=2147483647&&!!image;
  const create=()=>void act('save',async()=>{
    const data=image.startsWith('data:')?image:await asDataUrl(await presetPng());
    const asset=await json<Variant>('/api/studio/assets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({family,name,description,dimensions_m:dimensions,seed,reference_png_base64:data.split(',')[1]})});
    setSelected(asset.id);setCreating(false);setNotice(asset.reused?'Opened the matching saved variant. No generation request was sent.':'Design saved. Download its request package to generate it on ARC.');
  });
  return <div className="al-root">
    <button className="sw-text-button" onClick={onBack}>← Back to scenarios</button>
    <div className="sw-eyebrow"><Box size={14}/> REUSABLE DESIGNS <span>ASSET LIBRARY</span></div>
    <div className="al-heading"><div><h1>One design.<br/><em>Many possibilities.</em></h1><p>Generate a design once. Review it. Reuse it across scenarios.</p></div><button className="sw-generate" onClick={()=>setCreating(!creating)}><Plus size={16}/>{creating?'Close form':'New variant'}</button></div>
    <div className="al-scope"><span>CHAIR → dining / folding / armchair</span><span>COUCH → two-seat / sectional / other designs</span></div>
    <p className="al-intro">A furniture family can contain many designs. Ten copies of the same design share one asset. A different image, design, size or seed creates another variant.</p>
    {error&&<p className="sw-error" role="alert">{error}</p>}{notice&&<p className="sw-notice" role="status">{notice}</p>}
    <AssetAutomationPanel onAsset={id=>{setSelected(id);void refresh();}}/>
    <p className="sw-muted">Have a reference already? Use “New variant” for the optional image/upload and manual ARC handoff route.</p>
    {creating&&<section className="al-form" aria-label="New furniture variant">
      <div className="al-form-main"><p className="sw-eyebrow">01 / DEFINE THE DESIGN</p><div className="al-fields"><label>Furniture family<select value={family} onChange={e=>changeFamily(e.target.value)}><option value="couch">Couch</option><option value="chair">Chair</option></select></label><label>Variant name<input value={name} maxLength={80} onChange={e=>setName(e.target.value)}/></label></div><label>Describe this design<textarea value={description} maxLength={2000} onChange={e=>setDescription(e.target.value)}/></label><div className="al-fields al-measures">{['Width','Depth','Height'].map((label,i)=><label key={label}>{label} (m)<input aria-label={`${label} in metres`} type="number" min={.1} max={4} step={.01} value={dimensions[i]} onChange={e=>setDimensions(v=>v.map((n,index)=>index===i?Number(e.target.value):n))}/></label>)}<label>Seed<input type="number" min={0} max={2147483647} value={seed} onChange={e=>setSeed(Number(e.target.value))}/></label></div><p className="sw-muted">These are target dimensions. Blender preparation must check the actual generated shape and scale. The image guides Hunyuan; the description labels the design and does not act as a text-to-3D prompt.</p><button className="sw-generate" disabled={!!busy||!valid} onClick={create}>{busy==='save'?<Loader2 className="sw-spin" size={15}/>:<Check size={15}/>}Save design request <ArrowRight size={15}/></button></div>
      <div className="al-reference">{image?<img src={image} alt="Reference image for the new furniture variant"/>:<div className="al-no-image"><Box/><p>Upload a photo of this design.</p></div>}<label className="al-file"><Upload size={14}/>Choose reference PNG<input type="file" accept="image/png" disabled={!!busy} onChange={e=>{const f=e.target.files?.[0];if(f)void act('image',async()=>{if(f.size>8_000_000)throw new Error('Choose a PNG smaller than 8 MB.');setImage(await asDataUrl(f));});e.target.value='';}}/></label><small>Single object · clear background · whole object visible.<br/>Couch reference prepared for this POC; it is not generated geometry.</small></div>
    </section>}
    <div className="sw-results-title"><div><span className="sw-section-label">YOUR DESIGNS</span><h2>Furniture, with a history.</h2></div><span>{assets.length} variants</span></div>
    <div className="al-grid">{assets.map(a=><button key={a.id} className={`al-card ${selected===a.id?'selected':''}`} onClick={()=>setSelected(a.id)}><div className="al-card-image">{a.builtin?<Box size={48} strokeWidth={1}/>:<img src={fileUrl(a,generated(a)?'preview.png':'reference.png')} alt={`${generated(a)?'Generated preview':'Reference image'}: ${a.name}`}/>}<span>{a.builtin?'REVIEWED DEMO':generated(a)?'ARC OUTPUT':'REFERENCE ONLY'}</span></div><div className="al-card-info"><small>{a.family.toUpperCase()} / {a.id.slice(0,8)}</small><h3>{a.name}</h3><p>{a.dimensions_m.join(' × ')} m{a.builtin?'':' target'}</p><strong>{names[a.status]||a.status}</strong></div></button>)}</div>
    {current&&<section className="al-detail" aria-label="Selected furniture variant"><p className="sw-eyebrow">VARIANT / {current.id.slice(0,12)}</p><h2>{current.name}</h2><p>{current.description}</p>{current.builtin?<p>The existing room pipeline uses this reviewed chair. Its Blender file is connected through Connections.</p>:<>
      {generated(current)?<><Viewer asset={current}/><p className="sw-muted">Drag to orbit. Scroll to zoom. This displays the generated GLB with review lighting; physics is not running.</p><div className="sw-actions"><a href={fileUrl(current,'asset.glb')} download><ArrowDownToLine size={14}/>Download model for Blender</a><a href={fileUrl(current,'result.json')} download>Generation record</a><a href={fileUrl(current,'preview.png')} target="_blank" rel="noreferrer">Open ARC preview</a></div><div className="sw-actions"><button disabled={!!busy||['queued','running'].includes(current.blender?.status||'')} onClick={()=>void act('prepare',async()=>{await json(`/api/studio/assets/${current.id}/prepare`,{method:'POST'});})}><Box size={14}/>{['queued','running'].includes(current.blender?.status||'')?'Preparing in Blender…':'Clean, create collisions & export'}</button>{current.blender?.status==='complete'&&<><a href={`/api/studio/assets/${current.id}/blender/${current.blender.report?.collision_mesh_created?'furniture-unreal.blend':'furniture-review.blend'}`} download>Download review.blend</a><a href={`/api/studio/assets/${current.id}/blender/report.json`} download>Preparation report</a>{current.blender.report?.collision_mesh_created&&<><a href={`/api/studio/assets/${current.id}/blender/unreal-package.zip`} download>Download Unreal package</a><a href={`/api/studio/assets/${current.id}/blender/preview.png`} target="_blank" rel="noreferrer">Preparation preview</a><span>{current.blender.report.hull_count} convex collision pieces</span></>}</>}</div>{current.blender&&<p role="status">{current.blender.message}</p>}{current.blender?.report&&<p>Staged dimensions: {current.blender.report.staged_dimensions_m.map(n=>n.toFixed(3)).join(' × ')} m. Height is matched uniformly; width and depth retain the model’s proportions.</p>}<p className="sw-notice">Inspect the prepared Blender copy and collision fit before Unreal import. The package includes FBX, textures and explicit material instructions. Unreal collision cooking and physics still need verification; existing room demos use the reviewed chair.</p></>:<>
        <p className="sw-eyebrow">02 / GENERATE ON VT ARC</p><p>Download this request ZIP. Upload it through Open OnDemand, then submit one GPU job from the ARC repository folder.</p><div className="sw-actions"><a href={`/api/studio/assets/${current.id}/request.zip`} download><ArrowDownToLine size={14}/>Download ARC request</a></div><pre>bash arc/scripts/submit_hunyuan_variant.sh /path/to/asset-request-{current.id.slice(0,12)}.zip</pre><p className="sw-muted">Replace /path/to/ with the uploaded file’s location. ARC generates shape and PBR textures together, using the existing Hunyuan runtimes. The hosted planner key does not provide GPU access.</p>
        <p className="sw-eyebrow">03 / BRING THE RESULT BACK</p><p>When the job completes, download the result.zip printed in its output. Import it here to see the real generated model.</p><button className="sw-generate" disabled={!!busy} onClick={()=>{target.current=current.id;upload.current?.click();}}>{busy==='import'?<Loader2 size={15} className="sw-spin"/>:<Upload size={15}/>}Import ARC result.zip</button>
      </>}
    </>}</section>}
    <input hidden ref={upload} type="file" accept=".zip" onChange={e=>{const f=e.target.files?.[0];const id=target.current;if(f)void act('import',async()=>{if(f.size>240_000_000)throw new Error('Result ZIP must be smaller than 240 MB.');await json(`/api/studio/assets/${id}/result`,{method:'POST',headers:{'Content-Type':'application/zip'},body:f});setSelected(id);setNotice('ARC output imported and checked against this design request. Inspect the model before Blender preparation.');});e.target.value='';}}/>
    <footer className="sw-footer"><span>FIELDWORK / REUSABLE ASSET LIBRARY</span><span>REQUEST → ARC → REVIEW → PREPARE</span></footer>
  </div>;
}
