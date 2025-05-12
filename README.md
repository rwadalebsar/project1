# Todo App with Python Backend and React Frontend

## Description
A simple Todo application with a Python (FastAPI) backend and React frontend. This project demonstrates how to create a full-stack application with a RESTful API backend and a modern React frontend.

## Features
- RESTful API built with FastAPI
- Modern React frontend with hooks
- Create, read, update, and delete todo items
- Mark tasks as completed
- Responsive design

## Tech Stack
- **Backend**: Python, FastAPI
- **Frontend**: React, Vite, Axios
- **Styling**: CSS

## Installation

### Prerequisites
- Python 3.8+
- Node.js and npm

### Setup

```bash
# Clone the repository
git clone https://github.com/rwadalebsar/project1.git

# Navigate to the project directory
cd project1

# Set up the backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up the frontend
cd ../frontend
npm install
```

## Running the Application

### Option 1: Run both servers with a single script
```bash
# Make sure you're in the project root directory
chmod +x start-servers.sh
./start-servers.sh
```

### Option 2: Run servers separately

#### Backend Server
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```
The backend server will run at http://localhost:8000

#### Frontend Server
```bash
cd frontend
npm run dev
```
The frontend server will run at http://localhost:5173

## API Endpoints

- `GET /api/items` - Get all todo items
- `GET /api/items/{item_id}` - Get a specific todo item
- `POST /api/items` - Create a new todo item
- `PUT /api/items/{item_id}` - Update a todo item
- `DELETE /api/items/{item_id}` - Delete a todo item

## License
[MIT](https://choosealicense.com/licenses/mit/)
