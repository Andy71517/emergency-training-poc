"""Run SDXL in the existing ARC shape environment, then bind its actual PNG."""
import argparse
import json
from pathlib import Path

from asset_request import make_request
from automation_contract import IMAGE_MODEL, IMAGE_REVISION, reference_prompt, sha, validate_prompt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = validate_prompt(json.loads(args.prompt.read_bytes()))
    args.output.mkdir(parents=True, exist_ok=False)
    import torch
    from diffusers import StableDiffusionXLPipeline
    from huggingface_hub import hf_hub_download

    pipeline = StableDiffusionXLPipeline.from_pretrained(
        IMAGE_MODEL, revision=IMAGE_REVISION, torch_dtype=torch.float16,
        variant='fp16', use_safetensors=True,
    ).to('cuda')
    pipeline.enable_vae_slicing()
    prompt = reference_prompt(value)
    image = pipeline(prompt=prompt,
                     negative_prompt='cropped, multiple objects, extra legs, floating parts, room, people, text, logo',
                     num_inference_steps=30, guidance_scale=7.5, width=1024, height=1024,
                     generator=torch.Generator(device='cuda').manual_seed(value['seed'])).images[0]
    path = args.output / 'reference.png'
    image.convert('RGB').save(path)
    raw = path.read_bytes()
    request = make_request(value['family'], value['name'], value['description'],
                           value['dimensions_m'], value['seed'], raw)
    (args.output / 'request.json').write_text(json.dumps(request, indent=2)+'\n')
    # Retain the model's supplied terms rather than treating this image as measured evidence.
    license_path = hf_hub_download(IMAGE_MODEL, 'LICENSE.md', revision=IMAGE_REVISION)
    (args.output / 'image-LICENSE.md').write_bytes(Path(license_path).read_bytes())
    manifest = {'stage': 'reference_generated', 'model': IMAGE_MODEL, 'revision': IMAGE_REVISION,
                'settings': value['image_settings'], 'seed': value['seed'],
                'prompt': prompt, 'reference_sha256': sha(raw), 'image_conditioned_geometry': True}
    (args.output / 'image-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    main()
