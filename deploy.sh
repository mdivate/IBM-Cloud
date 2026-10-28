#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy.sh — Writing Pulse IBM Cloud Code Engine Deployment Script
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Prerequisites:
#   - IBM Cloud CLI installed: https://cloud.ibm.com/docs/cli
#   - Docker installed and running
#   - IBM Cloud Container Registry access
#   - Code Engine project created
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration — edit these values ────────────────────────────────────────
IBM_REGION="au-syd"
IBM_RESOURCE_GROUP="Default"
ICR_NAMESPACE="writing-pulse-ns"
IMAGE_NAME="writing-pulse"
IMAGE_TAG="v2.0"
CE_PROJECT="writing-pulse-project"
CE_APP_NAME="writing-pulse-app"
CE_PORT=8080
CE_CPU="1"
CE_MEMORY="4G"
CE_MIN_SCALE=1
CE_MAX_SCALE=3

# IBM Container Registry full image path
ICR_REGISTRY="au.icr.io"
FULL_IMAGE="${ICR_REGISTRY}/${ICR_NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"

# ── Colours for output ────────────────────────────────────────────────────────
GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }

# ── Step 1: Login to IBM Cloud ────────────────────────────────────────────────
info "Logging in to IBM Cloud (region: ${IBM_REGION})…"
ibmcloud login --apikey "${WATSONX_API_KEY}" -r "${IBM_REGION}" -g "${IBM_RESOURCE_GROUP}"
success "IBM Cloud login complete"

# ── Step 2: Target Code Engine project ───────────────────────────────────────
info "Targeting Code Engine project: ${CE_PROJECT}…"
ibmcloud ce project select --name "${CE_PROJECT}" 2>/dev/null || \
    ibmcloud ce project create --name "${CE_PROJECT}"
success "Code Engine project ready"

# ── Step 3: Login to IBM Container Registry ───────────────────────────────────
info "Logging in to IBM Container Registry…"
ibmcloud cr login --client docker
success "Container Registry login complete"

# ── Step 4: Create ICR namespace (idempotent) ─────────────────────────────────
info "Ensuring ICR namespace: ${ICR_NAMESPACE}…"
ibmcloud cr namespace-add "${ICR_NAMESPACE}" 2>/dev/null || true
success "Namespace ready"

# ── Step 5: Build Docker image ────────────────────────────────────────────────
info "Building Docker image: ${FULL_IMAGE}…"
docker build --platform linux/amd64 -t "${FULL_IMAGE}" .
success "Docker image built"

# ── Step 6: Push image to IBM Container Registry ─────────────────────────────
info "Pushing image to IBM Container Registry…"
docker push "${FULL_IMAGE}"
success "Image pushed: ${FULL_IMAGE}"

# ── Step 7: Create/update Code Engine application ────────────────────────────
info "Deploying to Code Engine application: ${CE_APP_NAME}…"
if ibmcloud ce application get --name "${CE_APP_NAME}" &>/dev/null; then
    # App exists — update it
    ibmcloud ce application update \
        --name "${CE_APP_NAME}" \
        --image "${FULL_IMAGE}" \
        --port "${CE_PORT}" \
        --cpu "${CE_CPU}" \
        --memory "${CE_MEMORY}" \
        --min-scale "${CE_MIN_SCALE}" \
        --max-scale "${CE_MAX_SCALE}"
    success "Application updated"
else
    # First deploy — create with secrets
    ibmcloud ce application create \
        --name "${CE_APP_NAME}" \
        --image "${FULL_IMAGE}" \
        --port "${CE_PORT}" \
        --cpu "${CE_CPU}" \
        --memory "${CE_MEMORY}" \
        --min-scale "${CE_MIN_SCALE}" \
        --max-scale "${CE_MAX_SCALE}" \
        --env "WATSONX_API_KEY=${WATSONX_API_KEY}" \
        --env "WATSONX_PROJECT_ID=${WATSONX_PROJECT_ID}" \
        --env "WATSONX_ENDPOINT=${WATSONX_ENDPOINT}" \
        --env "WATSONX_MODEL_ID=${WATSONX_MODEL_ID}"
    success "Application created"
fi

# ── Step 8: Get public URL ────────────────────────────────────────────────────
info "Fetching application URL…"
APP_URL=$(ibmcloud ce application get --name "${CE_APP_NAME}" --output json \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',{}).get('url',''))")

echo ""
echo "════════════════════════════════════════════════════════"
success "Writing Pulse deployed successfully!"
echo -e "${GREEN}  URL: ${APP_URL}${NC}"
echo "════════════════════════════════════════════════════════"
