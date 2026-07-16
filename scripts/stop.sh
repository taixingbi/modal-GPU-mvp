#!/usr/bin/env bash
# Stop/delete Modal services to avoid any cost.
# Usage:
#   ./scripts/stop.sh          # stop both apps (URLs go dead, code stays; redeploy to restore)
#   ./scripts/stop.sh --purge  # stop apps AND delete the model-cache volume

set -euo pipefail

echo "Stopping Modal apps..."
modal app stop modal-gpu-mvp || true
modal app stop diffusers-mvp || true

if [[ "${1:-}" == "--purge" ]]; then
  echo "Deleting huggingface-cache volume (SDXL weights will re-download next deploy)..."
  modal volume delete huggingface-cache --yes || true
fi

echo "Done. Current apps:"
modal app list
