#!/bin/bash


set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Getting roles"
yc resource-manager folder add-access-binding $FOLDER_ID --role serverless.containers.invoker --subject serviceAccount:$SA_ID 2>/dev/null || true
yc resource-manager folder add-access-binding $FOLDER_ID --role serverless.functions.invoker --subject serviceAccount:$SA_ID 2>/dev/null || true
yc resource-manager folder add-access-binding $FOLDER_ID --role ydb.editor --subject serviceAccount:$SA_ID 2>/dev/null || true
yc resource-manager folder add-access-binding $FOLDER_ID --role storage.viewer --subject serviceAccount:$SA_ID 2>/dev/null || true
yc resource-manager folder add-access-binding $FOLDER_ID --role container-registry.images.pusher --subject serviceAccount:$SA_ID 2>/dev/null || true

echo "Creating Container Registry..."
yc container registry create --name guestbook-registry --folder-id $FOLDER_ID 2>/dev/null || echo "  Registry already exists"
REGISTRY_ID=$(yc container registry get guestbook-registry --folder-id $FOLDER_ID --format json | jq -r .id)
echo "  Registry ID: $REGISTRY_ID"
yc container registry configure-docker
echo ""

echo "Creating Object Storage bucket..."
BUCKET_NAME="guestbook-frontend-$(date +%s)"
yc storage bucket create --name $BUCKET_NAME --folder-id $FOLDER_ID
echo "  Bucket: $BUCKET_NAME"
echo ""
