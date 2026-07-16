#!/usr/bin/env bash
# Redeploy both Modal apps (restores the persistent HTTPS endpoints).
# Usage: ./scripts/start.sh

set -euo pipefail

modal deploy app.py
modal deploy modal_diffusers.py

echo "Done. Current apps:"
modal app list
