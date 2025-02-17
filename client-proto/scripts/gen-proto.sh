#!/bin/bash

set -ex

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" && pwd -P)"

GRPC_ROOT=${SCRIPT_PATH}/../../nilvm/libs/node-api/proto

service_files=(
  "nillion/compute/v1/service.proto"
  "nillion/leader_queries/v1/service.proto"
  "nillion/membership/v1/service.proto"
  "nillion/payments/v1/service.proto"
  "nillion/permissions/v1/service.proto"
  "nillion/programs/v1/service.proto"
  "nillion/values/v1/service.proto"
)

standalone_files=(
  "nillion/auth/v1/token.proto"
)

chain_proto_files=(
  "nillion/meta/v1/tx.proto"
)

OUTPUT_DIR=${SCRIPT_PATH}/../src/nillion_client_proto

mkdir -p ${OUTPUT_DIR}

cd ${SCRIPT_PATH}/../src

# chain proto can't use better proto because of error
for file in "${chain_proto_files[@]}"; do
  python -m grpc_tools.protoc -I${GRPC_ROOT} --python_out=${OUTPUT_DIR} --pyi_out=${OUTPUT_DIR} $file
done

for file in "${service_files[@]}"; do
  python -m grpc_tools.protoc -I${GRPC_ROOT} --python_betterproto_out=nillion_client_proto $file
  service_path=$(dirname $file)
  # other generations overwrite this file where the service stubs are created, so we backup them and recover them later
  cp "${OUTPUT_DIR}/${service_path}/__init__.py" "${OUTPUT_DIR}/${service_path}/__init__.py.back"
done

for file in "${standalone_files[@]}"; do
  python -m grpc_tools.protoc -I${GRPC_ROOT} --python_betterproto_out=nillion_client_proto $file
done

# recover service stubs files overwritten
for file in "${service_files[@]}"; do
  service_path=$(dirname $file)
  mv "${OUTPUT_DIR}/${service_path}/__init__.py.back" "${OUTPUT_DIR}/${service_path}/__init__.py"
done
