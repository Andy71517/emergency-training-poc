"""Unreal-independent package preflight. Does not execute engine APIs."""
import hashlib
import json
import runpy
from pathlib import Path

import pytest

IMPORTER = runpy.run_path(str(Path(__file__).resolve().parents[2]/'unreal/scripts/import_furniture_package.py'))


def package(folder, report=None, plan=None):
    files = {'asset.fbx': b'explicit fixture only', 'setup_unreal58_chair_demo.py': b'# fixture only',
             'report.json': json.dumps(report or {'collision_mesh_created': True, 'hull_count': 4}).encode(),
             'material-plan.json': json.dumps(plan or {'mapping_review_required': False, 'slots': []}).encode()}
    for name, data in files.items():
        (folder/name).write_bytes(data)
    (folder/'export-manifest.json').write_text(json.dumps({'stage': 'unreal_import_candidate',
        'files': {n: hashlib.sha256(data).hexdigest() for n, data in files.items()}}))


def test_complete_package_and_changed_file(tmp_path):
    package(tmp_path)
    report, _ = IMPORTER['verify_package'](tmp_path)
    assert report['hull_count'] == 4
    (tmp_path/'asset.fbx').write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'):
        IMPORTER['verify_package'](tmp_path)


def test_invalid_collision_or_material_review_gate(tmp_path):
    package(tmp_path, report={'collision_mesh_created': True, 'hull_count': 33})
    with pytest.raises(ValueError, match='convex'):
        IMPORTER['verify_package'](tmp_path)
    package(tmp_path, plan={'mapping_review_required': True, 'slots': []})
    with pytest.raises(ValueError, match='material mapping'):
        IMPORTER['verify_package'](tmp_path)


def test_unbound_texture_is_rejected(tmp_path):
    package(tmp_path, plan={'mapping_review_required': False,
                           'slots': [{'base_color': {'file': '../private.png'}}]})
    with pytest.raises(ValueError, match='unbound'):
        IMPORTER['verify_package'](tmp_path)
