#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

mkdir -p png

for svg in svg/*.svg; do
    name=$(basename "$svg" .svg)
    rsvg-convert --width=2400 "$svg" -o "png/$name.png"
done

echo "PNG exportados en docs/graphs/png/"
