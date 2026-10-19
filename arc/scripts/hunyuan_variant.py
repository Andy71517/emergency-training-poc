"""Validate/extract a portable request, or export a completed Hunyuan variant."""
import argparse
import json
import shutil
import zipfile
from pathlib import Path

from asset_request import sha, validate_request

RESULT_NAMES = ('asset.glb', 'preview.png', 'shape-manifest.json', 'paint-manifest.json',
    'LICENSE', 'Notice.txt', 'source-patches.diff')


def unpack(source, requests):
    if source.stat().st_size > 9_000_000:
        raise ValueError('Request ZIP exceeds 9 MB.')
    with zipfile.ZipFile(source) as archive:
        if sorted(archive.namelist()) != ['reference.png', 'request.json']:
            raise ValueError('Expected only reference.png and request.json.')
        if any(i.file_size > 8_100_000 for i in archive.infolist()):
            raise ValueError('Request file too large.')
        image, raw = archive.read('reference.png'), archive.read('request.json')
    value = validate_request(json.loads(raw), image)
    folder = requests/value['asset_id']
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in [('reference.png', image), ('request.json', raw)]:
        target = folder/name
        if target.exists() and target.read_bytes() != data:
            # Semantically identical JSON may differ in formatting; never replace an active request.
            if name != 'request.json' or json.loads(target.read_bytes()) != value:
                raise ValueError('Existing request contents differ.')
        elif not target.exists():
            temp = target.with_suffix('.tmp')
            temp.write_bytes(data)
            temp.replace(target)
    return folder


def package(request_dir, run):
    value = validate_request(json.loads((request_dir/'request.json').read_bytes()), (request_dir/'reference.png').read_bytes())
    shape = json.loads((run/'shape/manifest.json').read_bytes())
    paint = json.loads((run/'paint/manifest.json').read_bytes())
    if shape.get('stage') != 'completed' or paint.get('stage') != 'completed':
        raise ValueError('Shape and paint stages must finish before export.')
    folder = run/'export'
    folder.mkdir(exist_ok=False)
    sources = {'asset.glb': run/'paint/chair-textured.glb', 'preview.png': run/'paint/preview.png',
        'shape-manifest.json': run/'shape/manifest.json', 'paint-manifest.json': run/'paint/manifest.json',
        **{name: run/'paint'/name for name in ('LICENSE', 'Notice.txt', 'source-patches.diff')},
        **{name: request_dir/name for name in ('request.json', 'reference.png')}}
    for name, source in sources.items():
        shutil.copy2(source, folder/name)
    result = {'contract': 'furniture-result-v1', 'asset_id': value['asset_id'], 'stage': 'completed',
        'shape_job': shape['job_id'], 'paint_job': paint['job_id'],
        'dimensions_are_requested_not_measured': True, 'physical_scale_verified': False,
        'collision_mesh_created': False, 'room_compatible': False,
        'paint_reproducibility': 'Upstream defaults; a saved result is reused, not regenerated for replay.',
        'files': {name: sha((folder/name).read_bytes()) for name in RESULT_NAMES}}
    (folder/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    output = run/'result.zip'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in folder.iterdir():
            archive.write(path, path.name)
    print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    extract = sub.add_parser('unpack')
    extract.add_argument('zip', type=Path)
    extract.add_argument('requests', type=Path)
    export = sub.add_parser('package')
    export.add_argument('request_dir', type=Path)
    export.add_argument('run', type=Path)
    args = parser.parse_args()
    if args.command == 'unpack':
        print(unpack(args.zip, args.requests))
    else:
        package(args.request_dir, args.run)


if __name__ == '__main__':
    main()
