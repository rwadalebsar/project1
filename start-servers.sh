#!/bin/bash

# Start the backend server
echo "Starting the backend server..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# Start the frontend server
echo "Starting the frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Function to handle script termination
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

# Set up trap to catch termination signals
trap cleanup SIGINT SIGTERM

# Keep the script running
echo "Both servers are running. Press Ctrl+C to stop."
wait
