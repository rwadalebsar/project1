# Build stage
FROM node:20-alpine as build

# Define build argument for API URL
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Update API URL in the build files
COPY update-api-url.js .
RUN node update-api-url.js

# Production stage
FROM nginx:alpine

# Copy the build output to replace the default nginx contents
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
