# Tank Level Monitoring Dashboard

## Description
A comprehensive dashboard for monitoring tank level sensors with data visualization, API integration, and machine learning for anomaly detection. This project demonstrates how to create a full-stack application with a Python backend and React frontend.

## Features
- RESTful API built with FastAPI
- External API integration for tank level data
- Interactive charts for visualizing tank level data
- Historical data tracking for up to 12 months
- Detailed views for recent data (3 days)
- Machine learning-based anomaly detection
- Responsive design for all device sizes
- Configurable API settings with fallback to mock data

## Tech Stack
- **Backend**: Python, FastAPI, Pandas, NumPy, scikit-learn
- **Frontend**: React, Vite, Axios, Recharts
- **Styling**: CSS with Grid Layout
- **Data Storage**: JSON-based file storage (easily replaceable with a database)

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

- `GET /api/tank-levels` - Get tank level readings (with optional filtering by days and tank ID)
- `POST /api/tank-levels` - Add a new tank level reading
- `GET /api/anomalies` - Get detected anomalies in tank level data
- `GET /api/stats` - Get statistics about tank levels

## External API Integration

The application is designed to work with external tank level sensor APIs. It includes:

1. **Configurable API Settings**: The frontend includes a configuration panel where you can set:
   - API URL
   - API Key
   - Tank ID
   - Option to use mock data for testing

2. **Fallback Mechanism**: If the external API is unavailable, the system falls back to cached data or generates mock data.

3. **API Service Layer**: The backend includes a dedicated service layer that handles:
   - API authentication
   - Data fetching and caching
   - Error handling
   - Mock data generation for development and testing

4. **Configuration File**: API settings can be configured in the `config.json` file in the backend directory.

## Machine Learning Implementation

The system uses the Isolation Forest algorithm from scikit-learn for anomaly detection. This algorithm is particularly well-suited for detecting outliers in time series data:

1. **How it works**: Isolation Forest isolates observations by randomly selecting a feature and then randomly selecting a split value between the maximum and minimum values of the selected feature.
2. **Advantages**:
   - Efficient with high-dimensional datasets
   - Requires minimal configuration (primarily the contamination parameter)
   - Works well with time series data
   - Doesn't make assumptions about the data distribution

3. **Implementation**: The backend processes tank level readings and identifies unusual patterns that might indicate sensor malfunctions, leaks, or other issues.

## Future Enhancements

1. **Database Integration**: Replace the JSON file storage with a proper database (PostgreSQL, MongoDB, etc.)
2. **Real-time Updates**: Implement WebSockets for real-time dashboard updates
3. **Advanced ML Models**: Implement more sophisticated anomaly detection algorithms
4. **User Authentication**: Add user login and role-based access control
5. **Multiple Tank Support**: Enhance the UI to better support multiple tanks
6. **Mobile App**: Develop a companion mobile application for on-the-go monitoring

## License
[MIT](https://choosealicense.com/licenses/mit/)
