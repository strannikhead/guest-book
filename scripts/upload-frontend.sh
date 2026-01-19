#!/bin/bash


set -e

echo "Uploading frontend..."
cd "$PROJECT_ROOT/frontend"
yc storage s3api put-object --bucket $BUCKET_NAME --key index.html --body index.html
echo "Successful"