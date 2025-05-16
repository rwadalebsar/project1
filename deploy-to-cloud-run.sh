#!/bin/bash
set -e

# Configuration
PROJECT_ID="tank-monitoring-dashboard"
REGION="us-central1"
BACKEND_SERVICE_NAME="tank-backend"
FRONTEND_SERVICE_NAME="tank-frontend"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment to Google Cloud Run...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "You are not logged in to gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Create project if it doesn't exist
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo -e "${YELLOW}Creating new Google Cloud project: $PROJECT_ID${NC}"
    gcloud projects create $PROJECT_ID
    gcloud config set project $PROJECT_ID
else
    echo "Using existing project: $PROJECT_ID"
    gcloud config set project $PROJECT_ID
fi

# Enable required APIs
echo -e "${YELLOW}Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com

# Create Artifact Registry repository
echo -e "${YELLOW}Setting up Artifact Registry...${NC}"
if ! gcloud artifacts repositories describe tank-repo --location=$REGION &> /dev/null; then
    gcloud artifacts repositories create tank-repo \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for Tank Monitoring Dashboard"
fi

# Build and push backend image
echo -e "${YELLOW}Building and pushing backend image...${NC}"
cd backend
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/tank-repo/backend:latest

# Deploy backend to Cloud Run
echo -e "${YELLOW}Deploying backend to Cloud Run...${NC}"
gcloud run deploy $BACKEND_SERVICE_NAME \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/tank-repo/backend:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10

# Get the backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo -e "${GREEN}Backend deployed at: $BACKEND_URL${NC}"

# Build and push frontend image with backend URL
cd ../frontend
echo -e "${YELLOW}Building and pushing frontend image...${NC}"
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/tank-repo/frontend:latest \
    --substitutions=_VITE_API_URL=$BACKEND_URL

# Deploy frontend to Cloud Run
echo -e "${YELLOW}Deploying frontend to Cloud Run...${NC}"
gcloud run deploy $FRONTEND_SERVICE_NAME \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/tank-repo/frontend:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 256Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5 \
    --set-env-vars="VITE_API_URL=$BACKEND_URL"

# Get the frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Backend URL: $BACKEND_URL${NC}"
echo -e "${GREEN}Frontend URL: $FRONTEND_URL${NC}"
echo -e "${YELLOW}Note: It may take a few minutes for the services to be fully available.${NC}"
