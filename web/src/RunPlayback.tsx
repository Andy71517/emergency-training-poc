import { ArrowDownToLine, Check, Film, Loader2, RefreshCw } from 'lucide-react';

export type RecordedClip = {
  scene_id:string;condition:string;map:string;frame_count:number;duration_seconds:number;
  measured_capture_fps:number;capture_warning?:string|null;maximum_displacement_m?:number;
  motion_check_passed?:boolean;settled_at_end?:boolean;
  controlled_input?:{object_id:string;applied_at_seconds:number;velocity_change_input_cm_per_s:number[]};
};
export type VideoStage = {status:string;message:string;run?:string;clips?:RecordedClip[];errors?:string[]};

export function RunPlayback({jobId,video,busy,onRetry}:{jobId:string;video?:VideoStage;busy:boolean;onRetry:()=>void}){
  if(!video)return <div className="sw-playback-empty"><Film size={25}/><div><strong>Your simulation, ready to watch here.</strong><p>Record a movement demo to get one clip per room. Existing room layouts and assets are reused.</p></div></div>;
  const working=['queued','running'].includes(video.status);
  const media=(scene:string,name:string)=>`/api/studio/jobs/${jobId}/recordings/${scene}/${name}?run=${video.run}`;
  return <section className="sw-playback" aria-label="Recorded Unreal playback">
    <div className="sw-playback-heading"><div><p className="sw-eyebrow">RECORDED IN UNREAL</p><h3>{working?'Preparing your playback':video.clips?.length?'Ready to watch':'Recording needs attention'}</h3></div>{working?<Loader2 className="sw-spin" size={20}/>:<Film size={23}/>}</div>
    <p role="status">{video.message}</p>
    {video.run&&<small className="sw-recording-id">RECORDING {video.run.slice(0,8).toUpperCase()} · SAVED PLAYBACK</small>}
    {video.clips?.map(clip=><article key={`${video.run}-${clip.scene_id}`} className="sw-video-card">
      <div className="sw-video-caption"><strong>{clip.scene_id.replace('_',' ')} <span>/ {clip.condition} aisle</span></strong><span>{clip.duration_seconds.toFixed(1)} s</span></div>
      <video controls playsInline preload="metadata" poster={media(clip.scene_id,'poster.png')} aria-label={`Recorded simulation ${clip.scene_id}`}>
        <source src={media(clip.scene_id,'clip.mp4')} type="video/mp4"/>
        Your browser cannot play this clip. Download the MP4 below.
      </video>
      <div className="sw-video-measures"><div><small>CHAIR MOVEMENT</small><strong>{clip.maximum_displacement_m===undefined?'Not measured':`${clip.maximum_displacement_m.toFixed(2)} m`}</strong></div><div><small>MOVEMENT CHECK</small><strong>{clip.motion_check_passed===true?<><Check size={13}/>Observed</>:clip.motion_check_passed===false?'Below 5 cm':'Not measured'}</strong></div><div><small>SETTLED AT END</small><strong>{clip.settled_at_end===true?'Yes':clip.settled_at_end===false?'No':'Not measured'}</strong></div></div>
      <p className="sw-video-detail">{clip.controlled_input?`${clip.controlled_input.object_id} received a fixed demo input at ${clip.controlled_input.applied_at_seconds.toFixed(1)} s. `:''}{clip.frame_count} captured frames · {clip.measured_capture_fps.toFixed(1)} frames/s measured. {clip.capture_warning||'Capture timing is approximate; saved frames are held between samples.'}</p>
      <div className="sw-actions"><a href={media(clip.scene_id,'clip.mp4')} download={`${clip.scene_id}-demo.mp4`}><ArrowDownToLine size={13}/>Download clip</a><a href={media(clip.scene_id,'capture.json')} download>Capture details</a></div>
    </article>)}
    {!!video.errors?.length&&<div role="alert" className="sw-error"><div>{video.errors.map(message=><p key={message}>{message}</p>)}</div></div>}
    <div className="sw-actions"><a href={`/api/studio/jobs/${jobId}/video-report`} download><ArrowDownToLine size={14}/>This recording’s observations</a>{['failed','partial','interrupted'].includes(video.status)&&<button disabled={busy} onClick={onRetry}><RefreshCw size={14}/>Retry encoding saved frames</button>}</div>
    <p className="sw-muted">A controlled visual test with demo physics settings. Movement and quiet-speed thresholds are measured; collision contacts and physical realism are not validated.</p>
  </section>;
}
