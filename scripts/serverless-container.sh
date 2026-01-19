#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

CONTAINER_NAME=${CONTAINER_NAME:-"guestbook-backend"}
REGISTRY_ID=${REGISTRY_ID}
IMAGE_NAME=${IMAGE_NAME:-"guestbook-backend"}
SERVICE_ACCOUNT_ID=${SERVICE_ACCOUNT_ID}

if [ -z "$REGISTRY_ID" ] || [ -z "$SERVICE_ACCOUNT_ID" ]; then
    echo "REGISTRY_ID and SERVICE_ACCOUNT_ID environment variables must be set"
    exit 1
fi

echo "Building..."
cd "$PROJECT_ROOT/backend"
docker build --platform linux/amd64 -t cr.yandex/${REGISTRY_ID}/${IMAGE_NAME}:latest .

echo "Pushing..."
docker push cr.yandex/${REGISTRY_ID}/${IMAGE_NAME}:latest

echo "Updating Container..."
yc serverless container revision deploy \
    --container-name ${CONTAINER_NAME} \
    --image cr.yandex/${REGISTRY_ID}/${IMAGE_NAME}:latest \
    --cores 1 \
    --memory 512MB \
    --execution-timeout 30s \
    --service-account-id ${SERVICE_ACCOUNT_ID} \
    --environment "YDB_ENDPOINT=${YDB_ENDPOINT}" \
    --environment "YDB_DATABASE=${YDB_DATABASE}" \
    --concurrency 3

echo "Successfully!"