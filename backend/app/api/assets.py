"""Local asset library routes; GPU execution remains an explicit ARC handoff."""
import io
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.app.studio.asset_automation import AssetAutomation
from backend.app.studio.assets import AssetLibrary
from backend.app.studio.service import local_settings


class VariantRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    family: str = Field(pattern='^(chair|couch)$')
    name: str = Field(min_length=3, max_length=80)
    description: str = Field(min_length=10, max_length=2000)
    dimensions_m: list[float] = Field(min_length=3, max_length=3)
    seed: int = Field(ge=0, le=2147483647, strict=True)
    reference_png_base64: str = Field(max_length=10_666_668)


def create_asset_router(service):
    router = APIRouter(prefix='/api/studio/assets', tags=['Furniture library'])
    library = AssetLibrary(service)
    automation = AssetAutomation(library)
    service.asset_automation = automation
    router.add_event_handler('shutdown', automation.close)

    def local(request):
        origin = request.headers.get('origin')
        if origin and urlparse(origin).hostname not in ('localhost', '127.0.0.1', '::1'):
            raise HTTPException(403, 'Local single-user workspace only.')

    def action(fn, *args):
        try:
            return fn(*args)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None

    async def limited_body(request, limit):
        data = bytearray()
        async for chunk in request.stream():
            if len(data) + len(chunk) > limit:
                raise HTTPException(413, 'Upload is too large.')
            data.extend(chunk)
        return bytes(data)

    @router.get('')
    def variants():
        return library.list()

    @router.get('/automation/config')
    def automation_config():
        values = local_settings()
        return {'ssh_configured': bool(values['ARC_SSH_TARGET'] and values['ARC_REMOTE_REPO']),
                'blender_configured': bool(values['BLENDER_EXECUTABLE'] and Path(values['BLENDER_EXECUTABLE']).is_file()),
                'image_provider': 'SDXL 1.0 on ARC', 'blender_transport': 'MCP stdio',
                'setup_document': 'docs/asset-automation-runbook.md'}

    @router.post('/automation/check')
    def automation_check(request: Request):
        local(request)
        return action(automation.transport.check)

    @router.get('/automation/jobs')
    def automation_jobs():
        return automation.list()

    @router.post('/automation/jobs', status_code=202)
    async def automate(request: Request):
        local(request)
        raw = await limited_body(request, 20000)
        import json
        try:
            body = json.loads(raw)
        except ValueError:
            raise HTTPException(400, 'Expected a furniture description.') from None
        return action(automation.submit, body)

    @router.post('/automation/jobs/{job_id}/resume', status_code=202)
    def resume_asset(job_id: str, request: Request):
        local(request)
        return action(automation.resume, job_id)

    @router.post('', status_code=201)
    async def create(request: Request):
        local(request)
        raw = await limited_body(request, 10_700_000)
        try:
            body = VariantRequest.model_validate_json(raw)
        except ValueError:
            raise HTTPException(400, 'Enter a name, design, dimensions, seed, and a PNG smaller than 8 MB.') from None
        return action(library.create, body.model_dump())

    @router.get('/{asset_id}/request.zip')
    def handoff(asset_id: str):
        raw = action(library.bundle, asset_id)
        return StreamingResponse(io.BytesIO(raw), media_type='application/zip',
            headers={'Content-Disposition': f'attachment; filename="asset-request-{asset_id[:12]}.zip"'})

    @router.post('/{asset_id}/result')
    async def upload(asset_id: str, request: Request):
        local(request)
        raw = await limited_body(request, 240_000_000)
        return action(library.import_result, asset_id, raw)

    @router.post('/{asset_id}/prepare', status_code=202)
    def prepare(asset_id: str, request: Request):
        local(request)
        return action(library.prepare, asset_id)

    @router.get('/{asset_id}/blender/{name}')
    def blender_file(asset_id: str, name: str):
        path = action(library.blender_file, asset_id, name)
        return FileResponse(path, filename=name, headers={'X-Content-Type-Options': 'nosniff'})

    @router.get('/{asset_id}/files/{name}')
    def file(asset_id: str, name: str):
        path = action(library.file, asset_id, name)
        return FileResponse(path, filename=name if name.endswith('.glb') else None,
            headers={'X-Content-Type-Options': 'nosniff'})

    return router
