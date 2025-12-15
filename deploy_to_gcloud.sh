#!/bin/bash
# Deploy LifeLink MLOps to Google Cloud

set -e

PROJECT_ID="lifelink-481222"
REGION="us-central1"
DASHBOARD_SERVICE="lifelink-dashboard"

echo "🚀 Deploying LifeLink MLOps to Google Cloud..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Build and push Dashboard image
echo "🔨 Building Dashboard image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$DASHBOARD_SERVICE:latest -f Dockerfile.dashboard .

# Deploy Dashboard to Cloud Run
echo "🚀 Deploying Dashboard to Cloud Run..."
gcloud run deploy $DASHBOARD_SERVICE \
    --image gcr.io/$PROJECT_ID/$DASHBOARD_SERVICE:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8501 \
    --memory 2Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

# Get the URL
DASHBOARD_URL=$(gcloud run services describe $DASHBOARD_SERVICE --region $REGION --format 'value(status.url)')

echo ""
echo "✅ Deployment Complete!"
echo "📊 Dashboard URL: $DASHBOARD_URL"
echo ""
echo "🔗 Access your MLOps Dashboard at: $DASHBOARD_URL"