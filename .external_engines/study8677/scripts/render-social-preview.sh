#!/usr/bin/env bash
# Re-renders docs/assets/social-preview.svg → docs/assets/social-preview.png
# at GitHub's recommended 1280×640 social-preview size.
#
# Uses svgexport (npx, no global install needed).

set -euo pipefail

SVG="docs/assets/social-preview.svg"
PNG="docs/assets/social-preview.png"

if [[ ! -f "$SVG" ]]; then
  echo "Missing $SVG"
  exit 1
fi

echo "→ Rendering $SVG → $PNG (1280×640)"
npx -y svgexport "$SVG" "$PNG" 1280:640
echo "✓ Wrote $PNG ($(du -h "$PNG" | cut -f1))"
