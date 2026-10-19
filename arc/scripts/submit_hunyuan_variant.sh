#!/bin/bash
# Run from the repository root. Reuses the already verified Hunyuan environments.
set -euo pipefail
source arc/scripts/load_arc_config.sh
source arc/scripts/hunyuan_texture_config.sh
[[ $# == 1 && -f "$1" ]] || { echo 'Usage: bash arc/scripts/submit_hunyuan_variant.sh /path/to/asset-request.zip' >&2; exit 2; }
for name in runtime-ready.env texture-ready.env; do
  [[ -f "$ARC_HUNYUAN_ROOT/metadata/$name" ]] || { echo "Missing $name. Verify the existing runtime first." >&2; exit 2; }
done
[[ -f "$ARC_HUNYUAN_CONTAINER" ]] || { echo 'Missing Hunyuan container.' >&2; exit 2; }
request_dir=$(python3 arc/scripts/hunyuan_variant.py unpack "$1" "$ARC_HUNYUAN_ROOT/requests")
asset_id=$(basename "$request_dir")
[[ "$asset_id" =~ ^[a-f0-9]{64}$ ]] || exit 2
if [[ -f "$ARC_HUNYUAN_ROOT/variants/$asset_id/result.zip" ]]; then
  echo "Already generated. Download: $ARC_HUNYUAN_ROOT/variants/$asset_id/result.zip"
  exit 0
fi
export HUNYUAN_VARIANT_ID="$asset_id"
mkdir -p arc/results
sbatch --account="$ARC_ACCOUNT" --partition="$ARC_GPU_PARTITION" --qos="$ARC_GPU_QOS" arc/jobs/generate_hunyuan_variant.sbatch
