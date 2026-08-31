#!/bin/bash

# Submit a small checkout job using the local ARC configuration. SBATCH
# directives cannot expand shell variables, so this wrapper supplies account
# and partition values at submission time instead of duplicating them in jobs.

set -euo pipefail

if [[ $# -ne 1 || ( "$1" != "cpu" && "$1" != "gpu" ) ]]; then
  echo "Usage: bash arc/scripts/submit_checkout.sh {cpu|gpu}" >&2
  exit 2
fi

# shellcheck source=load_arc_config.sh
source "$(dirname "$0")/load_arc_config.sh"

if [[ "$1" == "cpu" ]]; then
  sbatch --account="$ARC_ACCOUNT" --partition="$ARC_CPU_PARTITION" arc/jobs/verify_cpu.sbatch
else
  sbatch --account="$ARC_ACCOUNT" --partition="$ARC_GPU_PARTITION" arc/jobs/verify_a100.sbatch
fi
