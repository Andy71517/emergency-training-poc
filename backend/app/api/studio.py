"""Single-user, loopback-only studio HTTP interface."""
import re
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.app.studio.pipeline import Pipeline, connection_check
from backend.app.studio.service import SceneBatchService, settings


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    prompt: str = Field(min_length=10,max_length=8000)
    count: int = Field(ge=1,le=30,strict=True)
    seed: int = Field(ge=0,le=2147483647,strict=True)
    force_new: bool = Field(default=False,strict=True)


class ReplayRequest(BaseModel):
    seed: int = Field(ge=0,le=2147483647,strict=True)


def create_studio_router(service: SceneBatchService):
    router = APIRouter(prefix='/api/studio',tags=['Spatial studio'])
    pipeline = Pipeline(service)

    def local(request):
        origin = request.headers.get('origin')
        if origin and urlparse(origin).hostname not in ('localhost','127.0.0.1','::1'):
            raise HTTPException(403,'Local single-user workspace only.')

    def action(function, *args):
        try:
            return function(*args)
        except ValueError as exc:
            raise HTTPException(400,str(exc)) from None

    @router.get('/config')
    def config():
        key, model = settings()
        return {'configured':bool(key),'model':model,**pipeline.config()}

    @router.post('/connection-check')
    def check(request: Request):
        local(request)
        return action(connection_check)

    @router.get('/jobs')
    def jobs():
        pipeline.sync_engine()
        return service.list()

    @router.get('/trash')
    def trash_list():
        return service.trash_list()

    @router.post('/jobs/match')
    def match(body: GenerationRequest,request: Request):
        local(request)
        return service.find_match(body.prompt,body.count,body.seed)

    @router.post('/jobs',status_code=202)
    def generate(body: GenerationRequest, request: Request):
        local(request)
        try:
            return service.submit(body.prompt,body.count,body.seed,body.force_new)
        except ValueError as exc:
            raise HTTPException(400,str(exc)) from None

    @router.get('/jobs/{job_id}')
    def job(job_id: str):
        if not re.fullmatch(r'[a-f0-9]{32}',job_id):
            raise HTTPException(404,'Job not found')
        try:
            record=service.get(job_id)
            if record.get('trashed_at'):
                raise HTTPException(404,'Batch is in Trash. Restore it first.')
            return record
        except KeyError:
            raise HTTPException(404,'Job not found') from None

    @router.post('/jobs/{job_id}/trash')
    def trash(job_id: str,request: Request):
        local(request)
        job(job_id)
        return action(service.trash,job_id)

    @router.post('/jobs/{job_id}/restore')
    def restore(job_id: str,request: Request):
        local(request)
        if not re.fullmatch(r'[a-f0-9]{32}',job_id):
            raise HTTPException(404,'Job not found')
        try:
            return service.restore(job_id)
        except KeyError:
            raise HTTPException(404,'Job not found') from None

    @router.post('/jobs/{job_id}/engine/{action_name}',status_code=202)
    def engine_action(job_id: str, action_name: str, request: Request):
        local(request)
        job(job_id)
        return action(pipeline.enqueue_engine,job_id,action_name)

    @router.get('/jobs/{job_id}/chaos-report')
    def chaos_report(job_id: str):
        record=job(job_id)
        if record.get('pipeline',{}).get('simulation',{}).get('status')!='playback_reported':
            raise HTTPException(404,'No playback report available')
        return FileResponse(service.directory/job_id/'chaos-report.json',filename='chaos-report.json')

    @router.post('/jobs/{job_id}/video-retry',status_code=202)
    def video_retry(job_id: str,request: Request):
        local(request)
        job(job_id)
        return action(pipeline.retry_video,job_id)

    @router.get('/jobs/{job_id}/video-report')
    def video_report(job_id: str):
        record=job(job_id)
        stage=record.get('pipeline',{}).get('video',{})
        run=stage.get('run','')
        if not re.fullmatch(r'[a-f0-9]{32}',run):
            raise HTTPException(404,'Recording evidence not available')
        path=service.directory/job_id/'captures'/run/'observations.json'
        if not path.is_file():
            raise HTTPException(404,'Recording evidence missing')
        return FileResponse(path,filename='recorded-run-observations.json')

    @router.get('/jobs/{job_id}/recordings/{scene_id}/{name}')
    def recording(job_id: str,scene_id: str,name: str):
        record=job(job_id)
        stage=record.get('pipeline',{}).get('video',{})
        if stage.get('status') not in ('complete','partial') or name not in ('clip.mp4','poster.png','capture.json'):
            raise HTTPException(404,'Recording not available')
        run=stage.get('run','')
        if not re.fullmatch(r'[a-f0-9]{32}',run) or scene_id not in {c['scene_id'] for c in stage.get('clips',[])}:
            raise HTTPException(404,'Recording not found')
        path=service.directory/job_id/'captures'/run/scene_id/name
        if not path.is_file():
            raise HTTPException(404,'Recording file missing')
        return FileResponse(path,media_type='video/mp4' if name=='clip.mp4' else None,
            headers={'X-Content-Type-Options':'nosniff'})

    @router.post('/jobs/{job_id}/replay',status_code=202)
    def replay(job_id: str, body: ReplayRequest, request: Request):
        local(request)
        job(job_id)
        return action(service.replay,job_id,body.seed)

    @router.post('/jobs/{job_id}/blender',status_code=202)
    def blender(job_id: str, request: Request):
        local(request)
        job(job_id)
        return action(pipeline.blender,job_id)

    @router.get('/jobs/{job_id}/bundle/{target}')
    def bundle(job_id: str,target: str):
        job(job_id)
        if target not in ('spatial','unreal'):
            raise HTTPException(404,'Unknown bundle')
        path=action(pipeline.bundle,job_id,target)
        return FileResponse(path,filename=f'fieldwork-{target}-{job_id[:8]}.zip',media_type='application/zip')

    @router.post('/jobs/{job_id}/unreal-report')
    async def unreal_report(job_id: str,request: Request):
        local(request)
        job(job_id)
        raw=await request.body()
        if len(raw)>2_000_000:
            raise HTTPException(413,'Report exceeds 2 MB.')
        import json
        try:
            report=json.loads(raw)
        except ValueError:
            raise HTTPException(400,'Expected a JSON report.') from None
        if not isinstance(report,dict):
            raise HTTPException(400,'Expected a report object.')
        try:
            return action(pipeline.import_unreal_report,job_id,report)
        except (KeyError,TypeError,AttributeError):
            raise HTTPException(400,'Report does not match the Unreal assembly format.') from None

    @router.get('/jobs/{job_id}/blender-files/{name}')
    def blender_file(job_id: str,name: str):
        record=job(job_id)
        state=record.get('pipeline',{}).get('blender',{})
        if state.get('status')!='complete' or name not in ('rooms.blend','preview.png','report.json'):
            raise HTTPException(404,'Blender output not ready')
        run=state.get('run','')
        if not re.fullmatch(r'[a-f0-9]{32}',run):
            raise HTTPException(404,'Invalid worker output')
        path=service.directory/job_id/'blender'/run/name
        if not path.is_file():
            raise HTTPException(404,'Output missing')
        return FileResponse(path,headers={'X-Content-Type-Options':'nosniff'})

    @router.get('/jobs/{job_id}/files/{name}')
    def artifact(job_id: str,name: str):
        record = job(job_id)
        allowed = {'plan.json','manifest.json','asset-registry.json','request.json','preview.html'}
        allowed.update(f"{s['scene_id']}.{ext}" for s in record['scenes'] for ext in ('json','svg'))
        if record['status'] != 'review_ready' or name not in allowed:
            raise HTTPException(404,'Artifact not found')
        path = service.directory/job_id/name
        if not path.is_file():
            raise HTTPException(404,'Artifact not found')
        return FileResponse(path, headers={'X-Content-Type-Options':'nosniff'})
    return router

