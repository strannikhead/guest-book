echo "Creating API Gateway..."
cd "$PROJECT_ROOT"
cp openapi.yaml deploy-api.yaml

BUCKET_NAME_ESC=$(printf '%s\n' "$BUCKET_NAME" | sed 's/[\/&]/\\&/g')
CONTAINER_ID_ESC=$(printf '%s\n' "$CONTAINER_ID" | sed 's/[\/&]/\\&/g')
SA_ID_ESC=$(printf '%s\n' "$SERVICE_ACCOUNT_ID" | sed 's/[\/&]/\\&/g')

sed -i "s/\${BUCKET_NAME}/$BUCKET_NAME_ESC/g" deploy-api.yaml
sed -i "s/\${CONTAINER_ID}/$CONTAINER_ID_ESC/g" deploy-api.yaml
sed -i "s/\${SERVICE_ACCOUNT_ID}/$SA_ID_ESC/g" deploy-api.yaml

yc serverless api-gateway create --name guestbook-gateway --spec deploy-api.yaml --folder-id $FOLDER_ID 2>/dev/null || \
yc serverless api-gateway update guestbook-gateway --spec deploy-api.yaml --folder-id $FOLDER_ID

GATEWAY_URL=$(yc serverless api-gateway get guestbook-gateway --folder-id $FOLDER_ID --format json | jq -r .domain)
echo "Successful"