#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/load_arc_config.sh"
source "$(dirname "$0")/hunyuan_texture_config.sh"
for url in \
  "https://huggingface.co/tencent/Hunyuan3D-2.1/resolve/$ARC_HUNYUAN_PAINT_REVISION/hunyuan3d-paintpbr-v2-1/unet/diffusion_pytorch_model.bin" \
  "https://huggingface.co/facebook/dinov2-giant/resolve/$ARC_HUNYUAN_DINO_REVISION/model.safetensors" \
  "$ARC_HUNYUAN_ESRGAN_URL"; do
  curl --fail --location --silent --show-error --head --max-time 60 --output /dev/null "$url"
done
echo "Hunyuan paint, DINOv2, and Real-ESRGAN weights are accessible without a token."
