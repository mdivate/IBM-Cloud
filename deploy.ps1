# deploy.ps1 — Writing Pulse IBM Cloud Code Engine Deployment (Windows PowerShell)
# ─────────────────────────────────────────────────────────────────────────────
# Usage:
#   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\deploy.ps1
#
# Prerequisites:
#   - IBM Cloud CLI: winget install IBM.IBMCloudCLI
#   - Docker Desktop installed and running
# ─────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"

# ── Configuration — edit these values ────────────────────────────────────────
$IBM_REGION       = "au-syd"
$IBM_RG           = "Default"
$ICR_NAMESPACE    = "writing-pulse-ns"
$IMAGE_NAME       = "writing-pulse"
$IMAGE_TAG        = "v2.0"
$CE_PROJECT       = "writing-pulse-project"
$CE_APP_NAME      = "writing-pulse-app"
$CE_PORT          = 8080
$CE_CPU           = "1"
$CE_MEMORY        = "4G"

$ICR_REGISTRY     = "au.icr.io"
$FULL_IMAGE       = "${ICR_REGISTRY}/${ICR_NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"

# Load credentials from .env if present
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.+)$") {
            [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
    Write-Host "[OK] Loaded credentials from .env" -ForegroundColor Green
}

# ── Step 1: IBM Cloud login ────────────────────────────────────────────────
Write-Host "[INFO] Logging in to IBM Cloud (region: $IBM_REGION)..." -ForegroundColor Blue
ibmcloud login --apikey $env:WATSONX_API_KEY -r $IBM_REGION -g $IBM_RG
Write-Host "[OK] IBM Cloud login complete" -ForegroundColor Green

# ── Step 2: Target Code Engine project ────────────────────────────────────
Write-Host "[INFO] Targeting Code Engine project: $CE_PROJECT..." -ForegroundColor Blue
$result = ibmcloud ce project select --name $CE_PROJECT 2>&1
if ($LASTEXITCODE -ne 0) {
    ibmcloud ce project create --name $CE_PROJECT
}
Write-Host "[OK] Code Engine project ready" -ForegroundColor Green

# ── Step 3: ICR login ──────────────────────────────────────────────────────
Write-Host "[INFO] Logging in to IBM Container Registry..." -ForegroundColor Blue
ibmcloud cr login --client docker
Write-Host "[OK] Container Registry login complete" -ForegroundColor Green

# ── Step 4: ICR namespace ─────────────────────────────────────────────────
Write-Host "[INFO] Ensuring ICR namespace: $ICR_NAMESPACE..." -ForegroundColor Blue
ibmcloud cr namespace-add $ICR_NAMESPACE 2>&1 | Out-Null
Write-Host "[OK] Namespace ready" -ForegroundColor Green

# ── Step 5: Build Docker image ─────────────────────────────────────────────
Write-Host "[INFO] Building Docker image: $FULL_IMAGE..." -ForegroundColor Blue
docker build --platform linux/amd64 -t $FULL_IMAGE .
Write-Host "[OK] Docker image built" -ForegroundColor Green

# ── Step 6: Push to ICR ────────────────────────────────────────────────────
Write-Host "[INFO] Pushing image to IBM Container Registry..." -ForegroundColor Blue
docker push $FULL_IMAGE
Write-Host "[OK] Image pushed: $FULL_IMAGE" -ForegroundColor Green

# ── Step 7: Deploy to Code Engine ─────────────────────────────────────────
Write-Host "[INFO] Deploying to Code Engine: $CE_APP_NAME..." -ForegroundColor Blue
$appExists = ibmcloud ce application get --name $CE_APP_NAME 2>&1
if ($LASTEXITCODE -eq 0) {
    ibmcloud ce application update `
        --name $CE_APP_NAME `
        --image $FULL_IMAGE `
        --port $CE_PORT `
        --cpu $CE_CPU `
        --memory $CE_MEMORY
    Write-Host "[OK] Application updated" -ForegroundColor Green
} else {
    ibmcloud ce application create `
        --name $CE_APP_NAME `
        --image $FULL_IMAGE `
        --port $CE_PORT `
        --cpu $CE_CPU `
        --memory $CE_MEMORY `
        --min-scale 1 `
        --max-scale 3 `
        --env "WATSONX_API_KEY=$($env:WATSONX_API_KEY)" `
        --env "WATSONX_PROJECT_ID=$($env:WATSONX_PROJECT_ID)" `
        --env "WATSONX_ENDPOINT=$($env:WATSONX_ENDPOINT)" `
        --env "WATSONX_MODEL_ID=$($env:WATSONX_MODEL_ID)"
    Write-Host "[OK] Application created" -ForegroundColor Green
}

# ── Step 8: Get URL ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "[OK] Writing Pulse deployed to IBM Cloud!" -ForegroundColor Green
ibmcloud ce application get --name $CE_APP_NAME | Select-String "URL:"
Write-Host "=====================================================" -ForegroundColor Green
