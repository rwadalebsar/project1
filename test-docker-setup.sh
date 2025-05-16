#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing Docker setup for Tank Level Monitoring Dashboard...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Build the Docker images
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose build

# Run a quick test of the backend image
echo -e "${YELLOW}Testing backend image...${NC}"
docker run --rm -p 8000:8000 -d --name test-backend project1_backend
sleep 5

# Check if the backend is responding
if curl -s http://localhost:8000/api/health | grep -q "status"; then
    echo -e "${GREEN}Backend is working correctly!${NC}"
else
    echo -e "${RED}Backend test failed. Check the logs for more information.${NC}"
    docker logs test-backend
    docker stop test-backend
    exit 1
fi

# Stop the backend container
docker stop test-backend

# Run a quick test of the frontend image
echo -e "${YELLOW}Testing frontend image...${NC}"
docker run --rm -p 80:80 -d --name test-frontend project1_frontend
sleep 5

# Check if the frontend is responding
if curl -s http://localhost | grep -q "html"; then
    echo -e "${GREEN}Frontend is working correctly!${NC}"
else
    echo -e "${RED}Frontend test failed. Check the logs for more information.${NC}"
    docker logs test-frontend
    docker stop test-frontend
    exit 1
fi

# Stop the frontend container
docker stop test-frontend

echo -e "${GREEN}Docker setup test completed successfully!${NC}"
echo -e "${YELLOW}You can now run 'docker-compose up' to start the application.${NC}"
