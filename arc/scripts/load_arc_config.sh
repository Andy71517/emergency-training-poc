#!/bin/bash

# Load the intentionally untracked ARC project configuration for local use.
# Source this file from a login node or an approved ARC job wrapper.

set -euo pipefail

ARC_CONFIG_FILE="${ARC_CONFIG_FILE:-arc/.env}"

if [[ ! -f "$ARC_CONFIG_FILE" ]]; then
  echo "Missing $ARC_CONFIG_FILE. Copy arc/.env.example to arc/.env and fill in approved values." >&2
  exit 2
fi

# shellcheck source=/dev/null
source "$ARC_CONFIG_FILE"

required_variables=(
  ARC_ACCOUNT
  ARC_PROJECT_STORAGE_ROOT
  ARC_PROJECT_WORKSPACE
  ARC_CPU_PARTITION
  ARC_GPU_PARTITION
  ARC_GPU_QOS
)

for variable_name in "${required_variables[@]}"; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "$variable_name is required in $ARC_CONFIG_FILE." >&2
    exit 2
  fi
done

if [[ "$ARC_PROJECT_STORAGE_ROOT" != /projects/* || "$ARC_PROJECT_WORKSPACE" != /projects/* ]]; then
  echo "ARC project storage must be an approved absolute path under /projects." >&2
  exit 2
fi
