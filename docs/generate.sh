#!/bin/bash
set -e

OUTPUT_PATH=${1:?"Error: missing output path"}

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" && pwd -P)"

echo "Generating API documentation in ${OUTPUT_PATH}"

sphinx-build "$SCRIPT_PATH" "$OUTPUT_PATH"
sphinx-build -M markdown "$SCRIPT_PATH" "$OUTPUT_PATH"
