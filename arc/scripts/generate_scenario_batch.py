"""ARC hosted prompt -> bounded scene plan -> deterministic room layouts. Python 3.10+."""
import argparse
import getpass
import hashlib
import html
import json
import math
import os
import random
import tempfile
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

try:
    from .check_scenario_planner_access import safe_error_detail
except ImportError:  # Direct CLI execution from arc/scripts.
    from check_scenario_planner_access import safe_error_detail

ASSET = 'hunyuan_wooden_chair_8053348'
# Reviewed demo dimensions, not measurements of a real-world chair.
DIMENSIONS = [.542, .633, 1.0]
DEFAULT_PROMPT = ('Create three classroom-style room layouts using the reviewed wooden chair asset. '
                  'Include a visible exit and a designated aisle. Keep the aisle clear in two layouts '
                  'and obstruct it with chairs in the third. Record dimensions and assumptions.')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def parse_json(text):
    def invalid(value):
        raise ValueError('Non-finite JSON value: ' + value)
    return json.loads(text, object_pairs_hook=unique_pairs, parse_constant=invalid)


def number(value, low, high, name):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{name} must be between {low} and {high}.')


def validate_plan(plan, count=None):
    fields = {'title', 'room_width_m', 'room_depth_m', 'room_height_m', 'door_width_m',
              'aisle_width_m', 'chairs_per_room', 'variant_conditions', 'asset_ids',
              'assumptions', 'unsupported_requests'}
    if not isinstance(plan, dict) or set(plan) != fields:
        raise ValueError('Plan fields do not match the supported scene contract.')
    if not isinstance(plan['title'], str) or not 1 <= len(plan['title']) <= 120:
        raise ValueError('Invalid title.')
    for key, low, high in [('room_width_m', 6, 10), ('room_depth_m', 6, 10),
                          ('room_height_m', 2.5, 4), ('door_width_m', .9, 1.4),
                          ('aisle_width_m', 1.4, 2.0)]:
        number(plan[key], low, high, key)
    if type(plan['chairs_per_room']) is not int or not 4 <= plan['chairs_per_room'] <= 20:
        raise ValueError('chairs_per_room must be an integer from 4 to 20.')
    conditions = plan['variant_conditions']
    if not isinstance(conditions, list) or not 1 <= len(conditions) <= 30:
        raise ValueError('Expected 1-30 variant conditions.')
    if count is not None and len(conditions) != count:
        raise ValueError('Model returned a different variant count than requested.')
    if any(v not in ('clear', 'obstructed') for v in conditions):
        raise ValueError('Only clear and obstructed designated-aisle conditions are supported.')
    if plan['asset_ids'] != [ASSET]:
        raise ValueError('Only the reviewed chair is registered for this first batch.')
    for field in ('assumptions', 'unsupported_requests'):
        values = plan[field]
        if not isinstance(values, list) or len(values) > 20 or any(not isinstance(v, str) or len(v) > 500 for v in values):
            raise ValueError('Invalid ' + field)
    if plan['unsupported_requests']:
        raise ValueError('Unsupported request: ' + '; '.join(plan['unsupported_requests']))
    return plan


def overlap(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def footprint(obj):
    x, y, _ = obj['position_m']
    return [x - DIMENSIONS[0]/2, y - DIMENSIONS[1]/2,
            x + DIMENSIONS[0]/2, y + DIMENSIONS[1]/2]


def build_scene(plan, index, seed):
    rng = random.Random(seed)
    w, d, aisle = plan['room_width_m'], plan['room_depth_m'], plan['aisle_width_m']
    condition = plan['variant_conditions'][index]
    candidates = []
    for sign in (-1, 1):
        x = aisle/2 + .65
        while x + DIMENSIONS[0]/2 < w/2 - .3:
            y = 1.0
            while y + DIMENSIONS[1]/2 < d - 1.4:
                candidates.append([round(sign*x + rng.uniform(-.06, .06), 4),
                                   round(y + rng.uniform(-.06, .06), 4), 0.0])
                y += 1.1
            x += 1.0
    rng.shuffle(candidates)
    count = plan['chairs_per_room']
    needed = count - (condition == 'obstructed')
    if len(candidates) < needed:
        raise ValueError('Room cannot fit requested chair count under the spacing constraints.')
    positions = candidates[:needed]
    if condition == 'obstructed':
        positions.append([0.0, round(d - .85, 4), 0.0])
    objects = [{'instance_id': f'chair_{i:03}', 'asset_id': ASSET, 'position_m': position,
                'rotation_degrees': {'pitch': 0, 'yaw': 0, 'roll': 0}, 'scale': [1, 1, 1],
                'physics': {'mode': 'static_review', 'properties_calibrated': False}}
               for i, position in enumerate(positions)]
    corridor = [-aisle/2, .3, aisle/2, d]
    boxes = [footprint(o) for o in objects]
    for i, box in enumerate(boxes):
        if box[0] < -w/2 + .15 or box[2] > w/2 - .15 or box[1] < .15 or box[3] > d - .15:
            raise ValueError('Furniture footprint outside room.')
        if any(overlap(box, other) for other in boxes[:i]):
            raise ValueError('Furniture footprints overlap.')
    hits = [o['instance_id'] for o, box in zip(objects, boxes) if overlap(box, corridor)]
    if bool(hits) != (condition == 'obstructed'):
        raise ValueError('Layout does not meet designated-aisle condition.')
    return {'contract_version': 'spatial-draft-0.1', 'scene_id': f'room_{index+1:03}',
            'seed': seed, 'status': 'review_required', 'units': 'metres', 'up_axis': 'Z',
            'room': {'width_m': w, 'depth_m': d, 'height_m': plan['room_height_m'],
                     'wall_thickness_m': .15, 'door': {'wall': 'positive_y', 'centre_x_m': 0,
                     'width_m': plan['door_width_m'], 'height_m': 2.1}},
            'objects': objects, 'designated_aisle': {'bounds_xy_m': corridor, 'condition': condition,
            'overlapping_instances': hits, 'check': 'axis_aligned_footprint_overlap_only',
            'navigation_or_evacuation_validated': False}, 'source_plan_sha256': digest(plan)}


def svg(scene):
    w, d = scene['room']['width_m'], scene['room']['depth_m']
    scale = 55
    def x(v): return 40 + (v + w/2)*scale
    def y(v): return 50 + (d-v)*scale
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*scale+80}" height="{d*scale+100}" viewBox="0 0 {w*scale+80} {d*scale+100}">',
             '<rect width="100%" height="100%" fill="#10202d"/>',
             f'<text x="40" y="24" fill="white" font-family="sans-serif">{scene["scene_id"]}: {scene["designated_aisle"]["condition"]}</text>',
             f'<rect x="40" y="50" width="{w*scale}" height="{d*scale}" fill="#dce3e8" stroke="#8da4b5" stroke-width="6"/>']
    a = scene['designated_aisle']['bounds_xy_m']
    parts.append(f'<rect x="{x(a[0])}" y="{y(a[3])}" width="{(a[2]-a[0])*scale}" height="{(a[3]-a[1])*scale}" fill="#65cba4" opacity=".45"/>')
    door = scene['room']['door']['width_m']
    parts.append(f'<path d="M {x(-door/2)} 50 H {x(door/2)}" stroke="#42e6ae" stroke-width="9"/>')
    for obj in scene['objects']:
        b = footprint(obj)
        color = '#d05a47' if obj['instance_id'] in scene['designated_aisle']['overlapping_instances'] else '#a67635'
        parts.append(f'<rect x="{x(b[0])}" y="{y(b[3])}" width="{DIMENSIONS[0]*scale}" height="{DIMENSIONS[1]*scale}" fill="{color}" stroke="#513b25"/>')
    parts.append('</svg>')
    return ''.join(parts)


def ask_model(prompt, count, model, token=None):
    shape = {'title': 'Classroom chair layout', 'room_width_m': 8, 'room_depth_m': 8,
             'room_height_m': 3, 'door_width_m': 1.2, 'aisle_width_m': 1.6,
             'chairs_per_room': 12, 'variant_conditions': ['clear']*(count-1)+['obstructed'],
             'asset_ids': [ASSET], 'assumptions': ['Demo dimensions; no real evacuation validation.'],
             'unsupported_requests': []}
    system = ('You author bounded spatial plans, never code. Return ONE JSON object only, no Markdown. '
              'Use exactly these fields and types: '+canonical(shape)+'. '
              f'Return exactly {count} variant_conditions. Follow the requested mixture; do not silently change it. '
              'Room width/depth 6-10m, height 2.5-4m, door width .9-1.4m, aisle 1.4-2m; 4-20 chairs. '
              'Only classroom-like empty rectangular rooms, one centred positive-Y doorway and registered wooden chairs '
              'are supported. Put unsupported features (desks, agents, smoke, new assets, etc.) in unsupported_requests; '
              'do not substitute chairs for other assets. Record assumptions. No claim of emergency-training validity.')
    token = token or os.environ.get('ARC_LLM_API_KEY') or getpass.getpass('ARC LLM API key (hidden; not saved): ')
    if not token.strip():
        raise ValueError('No API key entered.')
    payload = {'model': model, 'messages': [{'role': 'system', 'content': system},
                {'role': 'user', 'content': prompt}], 'max_tokens': 4096}
    request = urllib.request.Request('https://llm-api.arc.vt.edu/api/v1/chat/completions',
                data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json',
                'Authorization': 'Bearer '+token.strip()}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read(2_000_000))
    except urllib.error.HTTPError as exc:
        raise ValueError(f'HTTP {exc.code}: '+safe_error_detail(exc.read(16_384), token)) from None
    content = data['choices'][0]['message'].get('content')
    if not isinstance(content, str) or not content.strip():
        raise ValueError('Model returned no final text. No fixture substituted; retry later.')
    # Never persist accidental credential echoes, including in the prompt or plan.
    if token.strip() in content or token.strip() in prompt:
        raise ValueError('Credential detected in content; nothing saved.')
    plan = validate_plan(parse_json(content), count)
    return plan, {'provider': 'arc_hosted_live', 'requested_model': model,
                  'returned_model': data.get('model'), 'response_content_sha256': hashlib.sha256(content.encode()).hexdigest()}


def write_package(out, plan, source, seed, prompt):
    out = Path(out).resolve()
    if out.exists():
        raise ValueError('Output already exists. Choose a fresh directory; no overwrite performed.')
    validate_plan(plan)
    scenes = [build_scene(plan, i, seed+i) for i in range(len(plan['variant_conditions']))]
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.scene-stage-', dir=out.parent) as temp:
        stage = Path(temp)/'package'
        stage.mkdir()
        def save(name, value):
            (stage/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        save('plan.json', plan)
        save('request.json', {'prompt': prompt, 'base_seed': seed, 'source': source,
                             'generated_at': datetime.now(UTC).isoformat()})
        save('asset-registry.json', {'assets': [{'asset_id': ASSET, 'dimensions_m': DIMENSIONS,
              'shape_job': '8052814', 'texture_job': '8053348', 'scale_is_assumed': True,
              'binary_assets_included': False, 'binding_status': 'requires_prepared_blender_asset_binding'}]})
        cards = []
        for scene in scenes:
            name = scene['scene_id']
            save(name+'.json', scene)
            (stage/(name+'.svg')).write_text(svg(scene), encoding='utf-8')
            cards.append(f'<article><h2>{html.escape(name)}</h2><img src="{name}.svg" alt="Top-down room layout"></article>')
        (stage/'preview.html').write_text('<!doctype html><meta charset="utf-8"><title>Room layout review</title>'
            '<style>body{background:#10202d;color:white;font:17px sans-serif;padding:24px}main{display:flex;flex-wrap:wrap;gap:24px}img{max-width:100%}article{max-width:520px}</style>'
            '<h1>'+html.escape(plan['title'])+'</h1><p>Spatial drafts for review. Green: designated aisle / doorway. '
            'Red: chair intersects the aisle. This is not a navigation or evacuation simulation.</p><main>'+''.join(cards)+'</main>',encoding='utf-8')
        files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir()}
        save('manifest.json', {'stage': 'spatial_drafts_ready', 'plan_sha256': digest(plan), 'files_sha256': files,
             'scene_count': len(scenes), 'blender_assembled': False, 'unreal_assembled': False})
        stage.rename(out)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt-file', type=Path)
    parser.add_argument('--count', type=int, default=3)
    parser.add_argument('--seed', type=int, default=20261018)
    parser.add_argument('--model', default=os.environ.get('ARC_LLM_MODEL', 'gpt-oss-120b'))
    parser.add_argument('--replay-plan', type=Path, help='Validated saved plan; performs no API call.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not 1 <= args.count <= 30:
        parser.error('--count must be 1-30')
    stamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')
    base = Path(os.environ.get('ARC_PROJECT_WORKSPACE', Path(__file__).resolve().parents[1]/'results'))
    output = args.output or base/'scenario-batches'/stamp
    if output.exists():
        parser.error('Output already exists; choose a fresh directory.')
    prompt = args.prompt_file.read_text(encoding='utf-8') if args.prompt_file else DEFAULT_PROMPT
    if not 10 <= len(prompt) <= 8000:
        parser.error('Prompt must contain 10-8000 characters.')
    if args.replay_plan:
        plan = validate_plan(parse_json(args.replay_plan.read_text(encoding='utf-8')))
        source = {'provider': 'saved_plan_replay', 'input_plan_sha256': digest(plan)}
        prompt = 'Replay of saved validated plan; see original package for its natural-language request.'
    else:
        if not args.prompt_file and args.count != 3:
            prompt = f'Create {args.count} classroom-style layouts with reviewed chairs, one centred exit and a designated aisle. Make the last layout obstructed and all preceding layouts clear.'
        print('Requesting a real ARC model plan; no asset generation or simulation started.', flush=True)
        plan, source = ask_model(prompt, args.count, args.model)
    path = write_package(output, plan, source, args.seed, prompt)
    print('Spatial drafts ready: '+str(path))
    print('Open preview.html for whole-batch review. Share plan.json and manifest.json.')
    print('Blender/Unreal assembly has not run. Replay uses the saved plan, not another LLM request.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, IndexError, OSError, urllib.error.URLError) as exc:
        raise SystemExit('Batch failed: '+str(exc)) from None
