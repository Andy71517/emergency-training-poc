"""Portable furniture-variant requests. Standard library only; also runs on ARC Python 3.10."""
import hashlib
import json
import math
import struct
import unicodedata
import zlib

MODEL = 'tencent/Hunyuan3D-2.1'
SHAPE_REVISION = '07d6dc9694e0ea942683bf6e3e374887d9f5b054'
PAINT_REVISION = '0b94677654c57bb9a6b6845cd7b704ccf551d327'
SOURCE_REVISION = '82920d643c0dc2f7bfd7255f45f62d386edfe60c'
DINO_REVISION = '611a9d42f2335e0f921f1e313ad3c1b7178d206d'
SETTINGS = {'pipeline': 'hunyuan-variant-v1', 'model': MODEL,
    'shape_revision': SHAPE_REVISION, 'paint_revision': PAINT_REVISION,
    'source_revision': SOURCE_REVISION, 'dino_revision': DINO_REVISION,
    'shape_steps': 30, 'octree_resolution': 256, 'paint_views': 6,
    'paint_resolution': 512, 'output_texture_size': 1024}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def validate_png(raw):
    """Check PNG framing, CRCs and dimensions without loading unbounded pixels."""
    if not 50 <= len(raw) <= 8_000_000 or raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Use a PNG image smaller than 8 MB.')
    offset, first, done = 8, True, False
    while offset + 12 <= len(raw):
        size = struct.unpack('>I', raw[offset:offset+4])[0]
        end = offset + 12 + size
        if end > len(raw):
            raise ValueError('Incomplete PNG image.')
        kind, data = raw[offset+4:offset+8], raw[offset+8:end-4]
        if zlib.crc32(kind + data) & 0xffffffff != struct.unpack('>I', raw[end-4:end])[0]:
            raise ValueError('PNG image checksum failed.')
        if first:
            if kind != b'IHDR' or size != 13:
                raise ValueError('Invalid PNG header.')
            width, height = struct.unpack('>II', data[:8])
            if not (64 <= width <= 4096 and 64 <= height <= 4096):
                raise ValueError('PNG dimensions must be 64–4096 pixels.')
            first = False
        offset = end
        if kind == b'IEND':
            done = size == 0 and offset == len(raw)
            break
    if not done:
        raise ValueError('Invalid PNG ending.')
    return width, height


def make_request(family, name, description, dimensions_m, seed, image):
    validate_png(image)
    def clean(value, low, high, label):
        if not isinstance(value, str):
            raise ValueError('Invalid ' + label)
        value = unicodedata.normalize('NFC', value.replace('\r\n', '\n').strip())
        if not low <= len(value) <= high:
            raise ValueError('Invalid ' + label)
        return value
    if family not in ('chair', 'couch'):
        raise ValueError('Choose chair or couch for this batch.')
    if type(seed) is not int or not 0 <= seed <= 2147483647:
        raise ValueError('Seed must be a whole number from 0 to 2147483647.')
    if not isinstance(dimensions_m, list) or len(dimensions_m) != 3 or any(
        type(v) not in (int, float) or not math.isfinite(v) or not .1 <= v <= 4 for v in dimensions_m):
        raise ValueError('Enter width, depth and height between 0.1 and 4 metres.')
    value = {'contract': 'furniture-request-v1', 'family': family,
        'name': clean(name, 3, 80, 'variant name'),
        'description': clean(description, 10, 2000, 'design description'),
        'dimensions_m': [float(v) for v in dimensions_m], 'seed': seed,
        'reference_sha256': sha(image), 'settings': SETTINGS.copy()}
    return dict(value, asset_id=sha(canonical(value).encode()))


def validate_request(value, image):
    if not isinstance(value, dict):
        raise ValueError('Expected an asset request.')
    try:
        expected = make_request(value['family'], value['name'], value['description'],
            value['dimensions_m'], value['seed'], image)
    except KeyError:
        raise ValueError('Incomplete asset request.') from None
    if value != expected:
        raise ValueError('Asset request contents, settings or reference image do not match its ID.')
    return value
