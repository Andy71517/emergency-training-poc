"""Encode only captured Unreal frames; never substitute a synthetic clip."""
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path


def encoder_available():
    return importlib.util.find_spec('imageio_ffmpeg') is not None


def encoder_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError,RuntimeError):
        raise ValueError('Video support is missing. Run .\\.venv\\Scripts\\python.exe -m pip install -e . in the project folder.') from None


def encode_scene(folder):
    folder=Path(folder).resolve()
    capture=json.loads((folder/'capture.json').read_text(encoding='utf-8'))
    frames=capture.get('frames',[])
    duration=capture.get('duration_seconds')
    if type(duration) not in (int,float) or not math.isfinite(duration) or not 0<duration<=30:
        raise ValueError('Invalid capture duration.')
    if capture.get('stage')!='unreal_viewport_frames' or not 2<=len(frames)<=120:
        raise ValueError('Fewer than two usable Unreal frames were saved. Check the Unreal viewport and rerun the recording.')
    previous=-1.0
    names=set()
    for frame in frames:
        name,timestamp=frame.get('file'),frame.get('time_seconds')
        if not isinstance(name,str) or not re.fullmatch(r'frame_\d{5}\.png',name) or name in names:
            raise ValueError('Invalid or duplicate captured frame name.')
        if type(timestamp) not in (int,float) or not math.isfinite(timestamp) or not previous<timestamp<=duration:
            raise ValueError('Invalid captured frame timing.')
        path=(folder/name).resolve()
        if path.parent!=folder or not path.is_file():
            raise ValueError('A captured Unreal frame is missing or outside the recording folder.')
        previous=timestamp
        names.add(name)
    lines=['ffconcat version 1.0']
    for i,frame in enumerate(frames):
        end=frames[i+1]['time_seconds'] if i+1<len(frames) else duration
        start=frame['time_seconds'] if i else 0
        lines.extend([f"file '{frame['file']}'",f'duration {max(0.001,end-start):.9f}'])
    lines.append(f"file '{frames[-1]['file']}'")
    listing=folder/'frames.ffconcat'
    listing.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    temporary=folder/'clip.partial.mp4'
    args=[encoder_path(),'-hide_banner','-loglevel','error','-y','-f','concat','-safe','1',
        '-i',str(listing),'-an','-t',str(duration),'-vf','fps=24,scale=960:540',
        '-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',
        '-movflags','+faststart',str(temporary)]
    result=subprocess.run(args,cwd=folder,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                          check=False,timeout=180,env={k:v for k,v in os.environ.items() if k!='ARC_LLM_API_KEY'})
    if result.returncode or not temporary.is_file() or temporary.stat().st_size<100:
        raise ValueError('Video encoding failed. Original captured frames were kept; rerun encoding or inspect the Unreal viewport.')
    temporary.replace(folder/'clip.mp4')
    shutil.copyfile(folder/frames[0]['file'],folder/'poster.png')
    span=frames[-1]['time_seconds']-frames[0]['time_seconds']
    return {'frame_count':len(frames),'duration_seconds':duration,
            'measured_capture_fps':(len(frames)-1)/span if span>0 else 0,
            'capture_warning':capture.get('capture_error'),
            'timing':'approximate_wall_clock_frame_capture','video_fps':24}
