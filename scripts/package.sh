#!/bin/bash -e

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" && pwd -P)"

# The python client core cannot be built statically (musl) so we build it with glibc (gnu) and we target a concrete
# glibc version (manylinux2014) to be compatible across different OSs and glibc versions
SUPPORTED_TARGETS=(
  "x86_64-unknown-linux-gnu"
  "aarch64-unknown-linux-gnu"
  "x86_64-apple-darwin"
  "aarch64-apple-darwin"
)

function package-client-core() {
    cd client-core
    TMP_FILE=$(mktemp)
    TARGET_TRIPLE=${1:?"Target triple is required"}

    if [[ "$TARGET_TRIPLE" == *linux* ]]; then
      uv run maturin build --compatibility manylinux2014 --zig --target "$TARGET_TRIPLE" --strip 2>&1 | tee "$TMP_FILE"
    else
      [[ "$TARGET_TRIPLE" == *darwin* ]] && [[ -z "$SDKROOT" ]] \
        && echo "To build a darwin target SDKROOT env var should be set to the path of macOS SDK for Mach Engine" && exit 1 || true
      uv run maturin build --zig --target "$TARGET_TRIPLE" --strip 2>&1 | tee "$TMP_FILE"
    fi

    wheel_path=$(cat "$TMP_FILE" | grep "Built wheel for" | sed -e "s|.*Built wheel for .* to \(.*\)|\1|g")

    wheel_name="$(basename "$wheel_path")"

    target_dir="./dist"
    mkdir -p "$target_dir"
    target_dir=$(realpath "$target_dir")

    cp "$wheel_path" "$target_dir"
    cd ..
}

function add-build-number {
  ls "${1:?"expected path as first arg"}" | grep whl | while read filename
  do
    new_name=$(echo $filename | sed -e "s|\([^-]*\)-\([^-]*\)-\(.*\)|\1-\2-$(date +%s)-\3|g")
    echo "Renaming $filename to $new_name"
    mv "$1/$filename" "$1/$new_name"
  done
}

cd $SCRIPT_PATH/..

for target in "${SUPPORTED_TARGETS[@]}"; do
  package-client-core "$target"
done
add-build-number client-core/dist

uv build --package nillion-client-proto -o client-proto/dist
add-build-number client-proto/dist

uv build --package nillion-client --sdist
uv build --package nillion-client --wheel
add-build-number dist