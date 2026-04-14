#!/usr/bin/env bash
# Open this repository as an Obsidian vault (macOS).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -d "/Applications/Obsidian.app" ]] || mdfind "kMDItemCFBundleIdentifier == 'md.obsidian'" 2>/dev/null | grep -q .; then
  open -a Obsidian "$REPO_ROOT"
else
  echo "Obsidian not found in /Applications. Install from https://obsidian.md/ or open this folder manually:" >&2
  echo "  $REPO_ROOT" >&2
  open "$REPO_ROOT"
fi
