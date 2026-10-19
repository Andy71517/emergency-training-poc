"""Real FFmpeg encoding with explicit fixture frames, plus browser media boundaries."""
import json
import struct
import time
import zlib

import imageio_ffmpeg
import pytest

from backend.app.studio.video import encode_scene
from backend.tests.test_studio import wait
from backend.tests.test_studio_pipeline import client_service


def write_png(path,color):
    def chunk(kind,data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    data=b''.join(b'\0'+bytes(color)*64 for _ in range(64))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',64,64,8,2,0,0,0))
                     +chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b''))


def capture_fixture(folder,scene_id='room_001'):
    folder.mkdir(parents=True)
    write_png(folder/'frame_00000.png',(180,40,20))
    write_png(folder/'frame_00001.png',(20,150,60))
    data={'stage':'unreal_viewport_frames','scene_id':scene_id,'duration_seconds':1.2,
          'frames':[{'file':'frame_00000.png','time_seconds':.1},{'file':'frame_00001.png','time_seconds':.6}]}
    (folder/'capture.json').write_text(json.dumps(data))
    return data


def test_real_encoding_and_invalid_frame_rejected(tmp_path):
    data=capture_fixture(tmp_path/'capture')
    metadata=encode_scene(tmp_path/'capture')
    assert metadata['frame_count']==2
    frames,seconds=imageio_ffmpeg.count_frames_and_secs(str(tmp_path/'capture/clip.mp4'))
    assert frames>=24 and 1.0<=seconds<=1.4
    decoder=imageio_ffmpeg.read_frames(str(tmp_path/'capture/clip.mp4'),pix_fmt='rgb24')
    next(decoder)
    samples=list(decoder)
    assert samples[0]!=samples[-1]
    data['frames'][0]['file']='../outside.png'
    (tmp_path/'capture/capture.json').write_text(json.dumps(data))
    with pytest.raises(ValueError,match='frame name'):
        encode_scene(tmp_path/'capture')


def test_record_result_becomes_playable_media(tmp_path,monkeypatch):
    client,service,_=client_service(tmp_path,monkeypatch)
    job=wait(service,service.submit('Three classroom layouts',3,42)['id'])
    queue=tmp_path/'engine';queue.mkdir()
    (queue/'heartbeat.json').write_text(json.dumps({'time':time.time(),'busy':False,
        'engine_version':'5.8.fake','capabilities':['assemble','simulate','record']}))
    job['pipeline']={'unreal':{'status':'assembly_reported','maps':[
        '/Game/EmergencyPOC/Rooms_test/Maps/'+s['scene_id'] for s in job['scenes']]}}
    service.save(job)
    base=f"/api/studio/jobs/{job['id']}"
    with client:
        assert client.post(base+'/engine/record').status_code==202
        command=json.loads(next(queue.glob('*.command.json')).read_text())
        observations=[]
        for scene,map_path in zip(job['scenes'],job['pipeline']['unreal']['maps']):
            capture_fixture(tmp_path/job['id']/'captures'/command['id']/scene['scene_id'],scene['scene_id'])
            observations.append({'map':map_path,'maximum_endpoint_displacement_m':.3,
                'target_maximum_displacement_m':.4,'motion_check_passed':True,'target_settled_at_end':True})
        result={'ok':True,'action':'record','job_id':job['id'],'run':command['id'],'observations':observations}
        (queue/(command['id']+'.result.json')).write_text(json.dumps(result))
        client.get('/api/studio/jobs')
        for _ in range(300):
            state=service.get(job['id']).get('pipeline',{}).get('video',{})
            if state.get('status') not in ('queued','running'):break
            time.sleep(.02)
        assert state['status']=='complete' and len(state['clips'])==3
        clip=client.get(base+'/recordings/room_001/clip.mp4',headers={'Range':'bytes=0-99'})
        assert clip.status_code==206 and clip.headers['content-type']=='video/mp4' and len(clip.content)==100
        assert client.get(base+'/recordings/room_001/poster.png').status_code==200
        assert client.get(base+'/recordings/not-a-scene/clip.mp4').status_code==404
        assert client.get(base+'/recordings/room_001/frames.ffconcat').status_code==404
        assert client.get(base+'/chaos-report').json()['action']=='record'
        assert client.get(base+'/video-report').json()['run']==command['id']
        # Retrying an encode must use the recording's own evidence, even after a later normal run.
        (tmp_path/job['id']/'chaos-report.json').write_text(json.dumps({'action':'simulate','observations':[]}))
        current=service.get(job['id']);current['pipeline']['video']['status']='failed';service.save(current)
        assert client.post(base+'/video-retry').status_code==202
        for _ in range(300):
            state=service.get(job['id'])['pipeline']['video']
            if state['status'] not in ('queued','running'):break
            time.sleep(.02)
        assert state['status']=='complete' and state['run']==command['id']
    service.pool.shutdown(wait=True)
