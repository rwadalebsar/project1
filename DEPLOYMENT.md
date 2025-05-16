# Deployment Guide for Tank Level Monitoring Dashboard

This guide provides instructions for deploying the Tank Level Monitoring Dashboard to Google Cloud Run.

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
2. Docker installed locally (for testing)
3. A Google Cloud account with billing enabled

## Local Testing with Docker

Before deploying to Google Cloud Run, you can test the application locally using Docker Compose:

```bash
# Build and start the containers
docker-compose up --build

# Access the application at http://localhost
```

## Deployment to Google Cloud Run

### Option 1: Using the Deployment Script

The easiest way to deploy is using the provided script:

```bash
# Make the script executable (if not already)
chmod +x deploy-to-cloud-run.sh

# Run the deployment script
./deploy-to-cloud-run.sh
```

The script will:
1. Create a Google Cloud project (if it doesn't exist)
2. Enable necessary APIs
3. Create an Artifact Registry repository
4. Build and push Docker images
5. Deploy the backend and frontend to Cloud Run
6. Configure the frontend to communicate with the backend

### Option 2: Using Cloud Build

For more advanced deployment options, you can use Cloud Build:

```bash
# Set your project ID
PROJECT_ID="tank-monitoring-dashboard"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com

# Create Artifact Registry repository
gcloud artifacts repositories create tank-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for Tank Monitoring Dashboard"

# Deploy using Cloud Build
gcloud builds submit --config=cloudbuild.yaml \
    --substitutions=_VERSION=v1,_REGION=us-central1
```

## Environment Variables

The following environment variables can be configured:

### Backend
- `ENVIRONMENT`: Set to `production` for production deployment

### Frontend
- `VITE_API_URL`: URL of the backend API service

## Accessing the Deployed Application

After deployment, you'll receive URLs for both the backend and frontend services:

- Backend API: `https://tank-backend-[hash]-[region].a.run.app`
- Frontend: `https://tank-frontend-[hash]-[region].a.run.app`

## Troubleshooting

### Common Issues

1. **CORS Errors**: If you see CORS errors in the browser console, check that the backend CORS configuration includes the frontend URL.

2. **Connection Refused**: Ensure the frontend is using the correct backend URL.

3. **Authentication Issues**: Make sure the Cloud Run services are configured to allow unauthenticated access, or set up proper authentication.

### Viewing Logs

```bash
# View backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=tank-backend" --limit=20

# View frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=tank-frontend" --limit=20
```

## Cleanup

To avoid incurring charges, you can delete the resources when they're no longer needed:

```bash
# Delete Cloud Run services
gcloud run services delete tank-backend --region=us-central1
gcloud run services delete tank-frontend --region=us-central1

# Delete Artifact Registry repository
gcloud artifacts repositories delete tank-repo --location=us-central1

# Delete the project (optional)
gcloud projects delete $PROJECT_ID
```
