#!/bin/bash

# Test admin login
echo "Testing admin login..."
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -v

echo -e "\n\n"

# Test user login
echo "Testing user login..."
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"password123"}' \
  -v

echo -e "\n\n"

# Test abdullah login
echo "Testing abdullah login..."
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"abdullah","password":"password123"}' \
  -v
