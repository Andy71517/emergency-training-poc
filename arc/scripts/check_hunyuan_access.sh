#!/bin/bash
# Small HTTP checks only: no model download, Python setup, or GPU allocation.
set -euo pipefail
source "$(dirname "$0")/load_arc_config.sh"
source "$(dirname "$0")/hunyuan_config.sh"
base="https://huggingface.co/tencent/Hunyuan3D-2.1/resolve/$ARC_HUNYUAN_MODEL_REVISION/hunyuan3d-dit-v2-1"
curl --fail --location --silent --show-error --max-time 60 --output /dev/null "$base/config.yaml"
curl --fail --location --silent --show-error --max-time 60 --head --output /dev/null "$base/model.fp16.ckpt"
echo "Hunyuan shape config and checkpoint are accessible without a token."
