"""Portable text-to-furniture input; contains no executable model instructions."""
import hashlib
import json
import math
import unicodedata

IMAGE_MODEL = 'stabilityai/stable-diffusion-xl-base-1.0'
IMAGE_REVISION = '462165984030d82259a11f4367a4eed129e94a7b'
IMAGE_SETTINGS = {'model': IMAGE_MODEL, 'revision': IMAGE_REVISION,
                  'steps': 30, 'guidance_scale': 7.5, 'size': [1024, 1024]}
FIELDS = {'family', 'name', 'description', 'dimensions_m', 'seed'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prompt_request(body):
    if not isinstance(body, dict) or set(body) != FIELDS or body['family'] not in ('chair', 'couch'):
        raise ValueError('Describe one chair or couch design.')
    value = dict(body)
    for field, low, high in [('name', 3, 80), ('description', 10, 2000)]:
        if not isinstance(value[field], str):
            raise ValueError('Invalid design text.')
        value[field] = unicodedata.normalize('NFC', value[field].replace('\r\n', '\n').strip())
        if not low <= len(value[field]) <= high:
            raise ValueError('Invalid design text length.')
    dims = value['dimensions_m']
    if not isinstance(dims, list) or len(dims) != 3 or any(
            type(n) not in (int, float) or not math.isfinite(n) or not .1 <= n <= 4 for n in dims):
        raise ValueError('Dimensions must be between 0.1 and 4 metres.')
    if type(value['seed']) is not int or not 0 <= value['seed'] <= 2147483647:
        raise ValueError('Invalid seed.')
    value['dimensions_m'] = [float(n) for n in dims]
    return dict(value, contract='furniture-prompt-v1', image_settings=IMAGE_SETTINGS)


def validate_prompt(value):
    if not isinstance(value, dict) or set(value) != FIELDS | {'contract', 'image_settings'}:
        raise ValueError('Invalid prompt contract.')
    expected = prompt_request({key: value[key] for key in FIELDS})
    if value != expected:
        raise ValueError('Prompt settings do not match the supported generator.')
    return expected


def reference_prompt(value):
    validate_prompt(value)
    return ('Studio product photograph of one ' + value['family'] + '. ' + value['description'] +
            ' Single complete object, front three-quarter view, centered with generous margins, '
            'all legs visible, physically coherent furniture, plain white background, '
            'soft even lighting, no room, no people, no text, no dimensions or watermark.')
