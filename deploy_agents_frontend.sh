#!/bin/bash
# Deploy LifeLink Agents (API) and Frontend to Google Cloud

set -e

PROJECT_ID="lifelink-481222"
REGION="us-central1"

echo "🚀 Deploying LifeLink Agents & Frontend to Google Cloud..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

echo ""
echo "=========================================="
echo "1️⃣  Building & Deploying API Backend"
echo "=========================================="

# Build API image
echo "🔨 Building API Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/lifelink-api:latest -f Dockerfile.api . --timeout=1200

# Deploy API to Cloud Run
echo "🚀 Deploying API to Cloud Run..."
gcloud run deploy lifelink-api \
    --image gcr.io/$PROJECT_ID/lifelink-api:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 5 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,LOG_LEVEL=INFO,WHATSAPP_ENABLED=false"

# Get API URL
API_URL=$(gcloud run services describe lifelink-api --region $REGION --format 'value(status.url)')
echo "✅ API deployed at: $API_URL"

echo ""
echo "=========================================="
echo "2️⃣  Building & Deploying Frontend"
echo "=========================================="

# Update frontend with API URL
echo "📝 Configuring frontend with API URL..."
cat > frontend/.env.production << EOF
VITE_API_URL=$API_URL
EOF

# Build Frontend image
echo "🔨 Building Frontend Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/lifelink-frontend:latest -f Dockerfile.frontend . --timeout=900

# Deploy Frontend to Cloud Run
echo "🚀 Deploying Frontend to Cloud Run..."
gcloud run deploy lifelink-frontend \
    --image gcr.io/$PROJECT_ID/lifelink-frontend:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 80 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3

# Get Frontend URL
FRONTEND_URL=$(gcloud run services describe lifelink-frontend --region $REGION --format 'value(status.url)')
echo "✅ Frontend deployed at: $FRONTEND_URL"

# Get Dashboard URL (if exists)
DASHBOARD_URL=$(gcloud run services describe lifelink-dashboard --region $REGION --format 'value(status.url)' 2>/dev/null || echo "Not deployed")

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "🌐 Frontend (React):     $FRONTEND_URL"
echo "🔗 API Backend:          $API_URL"
echo "📊 MLOps Dashboard:      $DASHBOARD_URL"
echo ""
echo "📖 API Documentation:    $API_URL/docs"
echo "❤️  API Health Check:    $API_URL/health"
echo ""
echo "🎯 Your LifeLink system is now live!"
