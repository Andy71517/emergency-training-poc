#!/bin/bash
# Fixed RPC entry point; accepts only the Python helper's allowlisted operations.
set -euo pipefail
source arc/scripts/load_arc_config.sh
source arc/scripts/hunyuan_config.sh
export ARC_HUNYUAN_ROOT ARC_ACCOUNT ARC_GPU_PARTITION ARC_GPU_QOS
exec python3 arc/scripts/remote_asset_control.py "$@"
