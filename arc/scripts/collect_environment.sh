#!/bin/bash

set -u

# shellcheck source=load_arc_config.sh
source "$(dirname "$0")/load_arc_config.sh"

echo "VT ARC environment snapshot"
echo "User: $(whoami)"
echo "Host: $(hostname)"
echo "Time: $(date --iso-8601=seconds)"
echo
echo "Storage summary:"
quota || true
echo
echo "Slurm associations:"
sacctmgr show assoc user="$USER" format=Cluster,Account,User,Partition,QOS%50 || true
echo
echo "Visible partitions:"
sinfo --format="%P %a %l %D %G" || true
echo
echo "Project root:"
ls -ld "$ARC_PROJECT_STORAGE_ROOT" || true
echo "Project workspace:"
ls -ld "$ARC_PROJECT_WORKSPACE" || true
