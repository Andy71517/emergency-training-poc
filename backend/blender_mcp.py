"""Project-scoped stdio MCP. Runs trusted Blender operations, never generated code."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP

REPO = Path(__file__).resolve().parents[1]
server = FastMCP('FIELDWORK Blender preparation')


def paths(asset_id, revision, run_id=None):
    if not re.fullmatch('[a-f0-9]{64}', asset_id) or not re.fullmatch('[a-f0-9]{32}', revision):
        raise ValueError('Invalid asset identity.')
    root = Path(os.environ['BLENDER_ASSET_ROOT']).resolve()
    folder = (root/asset_id).resolve()
    source = (folder/'results'/revision/'asset.glb').resolve()
    request = (folder/'request.json').resolve()
    if not source.is_relative_to(root) or not request.is_relative_to(root) or not source.is_file() or not request.is_file():
        raise ValueError('Asset source unavailable inside the configured library.')
    if run_id is None:
        return source, request, None
    if not re.fullmatch('[a-f0-9]{32}', run_id):
        raise ValueError('Invalid preparation run.')
    output = (folder/'blender'/run_id).resolve()
    if not output.is_relative_to(root):
        raise ValueError('Invalid preparation folder.')
    return source, request, output


@server.tool()
def inspect_asset(asset_id: str, result_revision: str) -> dict:
    """Inspect a saved generated asset binding without changing any geometry."""
    source, request, _ = paths(asset_id, result_revision)
    value = json.loads(request.read_bytes())
    return {'asset_id': asset_id, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'source_bytes': source.stat().st_size, 'target_dimensions_m': value['dimensions_m']}


@server.tool()
def prepare_asset(asset_id: str, result_revision: str, run_id: str,
                  yaw_degrees: Literal[0, 90, 180, 270] = 0) -> dict:
    """Clean a copy, decompose collision proxies and export Blender/FBX for review.

    Uses fixed scripts and bounded settings. Does not certify physics or execute
    user/model Python. Sources are preserved; output folders cannot be reused.
    """
    source, request, output = paths(asset_id, result_revision, run_id)
    executable = Path(os.environ['BLENDER_EXECUTABLE'])
    if not executable.is_file():
        raise ValueError('Configure a valid Blender executable.')
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=False)
    worker = REPO/'scripts/blender/prepare_unreal_asset.py'
    base = [str(executable), '--background', '--factory-startup', '--python-exit-code', '1',
            '--python', str(worker), '--']
    with (output/'worker.log').open('wb') as log:
        def run(command, timeout):
            log.write(('Starting '+('Blender' if command[0] == str(executable) else 'collision decomposition')+'\n').encode())
            log.flush()
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                    timeout=timeout, check=False)
            log.write(('Exit code '+str(result.returncode)+'\n').encode())
            log.flush()
            if result.returncode:
                raise ValueError('Preparation stage failed. Its local worker log was preserved.')
        run(base+['cleanup', '--source', str(source), '--request', str(request),
                  '--output', str(output), '--yaw', str(yaw_degrees)], 900)
        run([sys.executable, '-m', 'backend.app.studio.convex_parts',
             str(output/'collision-input.npz'), str(output/'collisions.json')], 900)
        run(base+['export', '--output', str(output)], 900)
    if hashlib.sha256(source.read_bytes()).hexdigest() != before:
        raise ValueError('Source hash changed unexpectedly.')
    report = json.loads((output/'report.json').read_bytes())
    if report.get('asset_id') != asset_id or report.get('source_sha256') != before or report.get('collision_mesh_created') is not True:
        raise ValueError('Unexpected Blender preparation report.')
    package_output(output, source, request)
    return report


def package_output(output, source, request):
    names = ['furniture-unreal.blend', 'asset.fbx', 'report.json', 'material-plan.json',
             'export-manifest.json', 'preview.png']
    for name in ('import_furniture_package.py', 'setup_unreal58_chair_demo.py'):
        shutil.copy2(REPO/'unreal/scripts'/name, output/name)
        names.append(name)
    (output/'START-HERE.txt').write_text(
        'Open furniture-unreal.blend to review the cleaned mesh and UCX hulls.\n'
        'In Unreal 5.8 with Python Editor Script Plugin enabled, execute import_furniture_package.py\n'
        'from this extracted folder. It creates fresh content and validates imported hull count/size.\n'
        'No simulation is started. Review collision fit and materials before using the asset.\n')
    names.append('START-HERE.txt')
    names += [str(p.relative_to(output)).replace('\\', '/') for p in (output/'textures').glob('*')]
    provenance = output/'provenance'
    provenance.mkdir(exist_ok=True)
    for parent, filenames in [(source.parent, ('LICENSE', 'Notice.txt', 'source-patches.diff',
                                               'shape-manifest.json', 'paint-manifest.json')),
                              (request.parent, ('request.json', 'automation-image-LICENSE.md',
                                                'automation-image-manifest.json', 'automation-prompt.json'))]:
        for name in filenames:
            if (parent/name).is_file():
                shutil.copy2(parent/name, provenance/name)
                names.append('provenance/'+name)
    manifest = json.loads((output/'export-manifest.json').read_bytes())
    manifest['files'] = {name: hashlib.sha256((output/name).read_bytes()).hexdigest()
                         for name in names if name != 'export-manifest.json'}
    (output/'export-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    with zipfile.ZipFile(output/'unreal-package.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.write(output/name, name)


if __name__ == '__main__':
    server.run(transport='stdio')
