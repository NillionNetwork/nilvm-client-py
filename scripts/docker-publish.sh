 #!/bin/bash -e

SELF_VERSION=$(
  docker inspect python-client-builder:latest --format "{{{{range .Config.Env}}{{{{println .}}{{{{end}}" \
  | grep "SELF_VERSION" \
  | sed -e "s|SELF_VERSION=\(.*\)|\1|g"
)
docker tag python-client-builder:latest public.ecr.aws/x8g8t2h7/python-client-builder:0.1.0
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
docker push public.ecr.aws/x8g8t2h7/python-client-builder:0.1.0