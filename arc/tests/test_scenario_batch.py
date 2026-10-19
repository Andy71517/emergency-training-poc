"""Offline contract/geometry/replay tests; does not claim live API verification."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('batch', SCRIPTS/'generate_scenario_batch.py')
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def fixture():
    return {'title': 'Offline test fixture', 'room_width_m': 8, 'room_depth_m': 8,
            'room_height_m': 3, 'door_width_m': 1.2, 'aisle_width_m': 1.6,
            'chairs_per_room': 12, 'variant_conditions': ['clear', 'clear', 'obstructed'],
            'asset_ids': [batch.ASSET], 'assumptions': ['Test fixture, not live output'],
            'unsupported_requests': []}


class BatchTests(unittest.TestCase):
    def test_invalid_plans(self):
        for key, value in [('room_width_m', float('nan')), ('chairs_per_room', True),
                           ('chairs_per_room', 99), ('asset_ids', ['invented']),
                           ('unsupported_requests', ['smoke simulation']),
                           ('variant_conditions', ['unknown'])]:
            with self.subTest(key=key):
                plan = fixture()
                plan[key] = value
                with self.assertRaises(ValueError):
                    batch.validate_plan(plan)
        with self.assertRaises(ValueError):
            batch.validate_plan(fixture(), 5)
        for text in ('{"x":1,"x":2}', '{"x":NaN}'):
            with self.assertRaises(ValueError):
                batch.parse_json(text)

    def test_layout_constraints_across_sizes_and_seeds(self):
        for width in (6, 8, 10):
            for depth in (6, 8, 10):
                plan = fixture()
                plan.update(room_width_m=width, room_depth_m=depth, chairs_per_room=6)
                for seed in range(20):
                    for i, condition in enumerate(plan['variant_conditions']):
                        scene = batch.build_scene(batch.validate_plan(plan), i, seed)
                        self.assertEqual(len(scene['objects']), 6)
                        self.assertEqual(bool(scene['designated_aisle']['overlapping_instances']), condition == 'obstructed')

    def test_overfull_room_rejected(self):
        plan = fixture()
        plan.update(room_width_m=6, room_depth_m=6, aisle_width_m=2, chairs_per_room=20)
        with self.assertRaises(ValueError):
            batch.build_scene(plan, 0, 42)

    def test_replay_and_no_overwrite(self):
        plan = fixture()
        restored = batch.parse_json(batch.canonical(plan))
        self.assertEqual(batch.build_scene(plan, 0, 42), batch.build_scene(restored, 0, 42))
        self.assertNotEqual(batch.build_scene(plan, 0, 42), batch.build_scene(plan, 0, 43))
        before = copy.deepcopy(plan)
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'batch'
            batch.write_package(output, plan, {'provider': 'offline_test_fixture'}, 42, 'Test fixture request')
            self.assertEqual(plan, before)
            manifest = json.loads((output/'manifest.json').read_text())
            for name, digest in manifest['files_sha256'].items():
                import hashlib
                self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(), digest)
            with self.assertRaises(ValueError):
                batch.write_package(output, plan, {}, 42, 'Test fixture request')


if __name__ == '__main__':
    unittest.main()
