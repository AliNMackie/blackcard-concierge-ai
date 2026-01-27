#!/bin/bash
set -e

# ==================================================================================
# Elite Concierge AI - Backend Deployment Script
# ==================================================================================
# Usage: ./deploy_backend.sh <PROJECT_ID> [REGION]
# Example: ./deploy_backend.sh my-gcp-project europe-west2
# ==================================================================================

PROJECT_ID=$1
REGION=${2:-europe-west2}
SERVICE_NAME="elite-concierge" # Must match 'service_name' variable in Terraform
REPO_NAME="${SERVICE_NAME}-repo"
CLOUD_RUN_SERVICE="${SERVICE_NAME}-api"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required."
  echo "Usage: ./deploy_backend.sh <PROJECT_ID> [REGION]"
  exit 1
fi

echo "========================================================"
echo "Deploying Backend for Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $CLOUD_RUN_SERVICE"
echo "========================================================"

# 1. Image Name Construction
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/backend:latest"

echo "[1/3] Building and Pushing Docker Image..."
echo "      Tag: $IMAGE_URI"

# We build from the 'backend' directory context, assuming script is run from repo root
if [ -d "backend" ]; then
    gcloud builds submit backend --tag "$IMAGE_URI" --project "$PROJECT_ID"
else
    echo "Error: 'backend' directory not found. Please run this script from the repository root."
    exit 1
fi

echo "[2/3] Updating Cloud Run Service..."
# Note: We assume the service is already created via Terraform. 
# We just update the image modification.

gcloud run services update "$CLOUD_RUN_SERVICE" \
  --image "$IMAGE_URI" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --quiet

echo "[3/3] Deployment Verification"
SERVICE_URL=$(gcloud run services describe "$CLOUD_RUN_SERVICE" --platform managed --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)')

echo "========================================================"
echo "SUCCESS: Deployment Complete"
echo "Service URL: $SERVICE_URL"
echo "Health Check: $SERVICE_URL/health"
echo "========================================================"
