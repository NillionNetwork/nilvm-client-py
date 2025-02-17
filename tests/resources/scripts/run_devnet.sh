#!/usr/bin/env bash
set -em

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" && pwd -P)"

MAX_WAIT_SECONDS=${MAX_WAIT_SECONDS:-30}

if [[ "$1" == "background" ]]; then
  nillion-devnet >"${SCRIPT_PATH}/devnet.log" &
  echo "Waiting for the environment file to be written"
  count=0
  while ! grep "environment file written" "${SCRIPT_PATH}/devnet.log"; do
    [[ $count -eq $MAX_WAIT_SECONDS ]] && echo "Timeout waiting for the environment file to be written" && exit 1
    sleep 1
    count=$((count + 1))
  done
else
  nillion-devnet
fi
