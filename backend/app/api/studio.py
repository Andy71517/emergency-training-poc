"""Single-user, loopback-only studio HTTP interface."""
import re
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.app.studio.service import SceneBatchService, settings


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    prompt: str = Field(min_length=10,max_length=8000)
    count: int = Field(ge=1,le=30,strict=True)
    seed: int = Field(ge=0,le=2147483647,strict=True)


def create_studio_router(service: SceneBatchService):
    router = APIRouter(prefix='/api/studio',tags=['Spatial studio'])

    @router.get('/config')
    def config():
        key, model = settings()
        return {'configured':bool(key),'model':model,'blender_connected':False,'unreal_connected':False}

    @router.get('/jobs')
    def jobs():
        return service.list()

    @router.post('/jobs',status_code=202)
    def generate(body: GenerationRequest, request: Request):
        origin = request.headers.get('origin')
        if origin and urlparse(origin).hostname not in ('localhost','127.0.0.1','::1'):
            raise HTTPException(403,'Local single-user workspace only.')
        try:
            return service.submit(body.prompt,body.count,body.seed)
        except ValueError as exc:
            raise HTTPException(400,str(exc)) from None

    @router.get('/jobs/{job_id}')
    def job(job_id: str):
        if not re.fullmatch(r'[a-f0-9]{32}',job_id):
            raise HTTPException(404,'Job not found')
        try:
            return service.get(job_id)
        except KeyError:
            raise HTTPException(404,'Job not found') from None

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
