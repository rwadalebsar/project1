# Tank Level Monitoring Dashboard

## Description
A comprehensive dashboard for monitoring tank level sensors with data visualization, API integration, and machine learning for anomaly detection. This project demonstrates how to create a full-stack application with a Python backend and React frontend.

## Features
- RESTful API built with FastAPI
- External API integration for tank level data
- Interactive charts for visualizing tank level data
- Historical data tracking for up to 12 months
- Detailed views for recent data (3 days)
- Machine learning-based anomaly detection with user feedback system
- Modern UI with responsive design for all device sizes
- Dark mode sidebar with intuitive navigation
- Card-based dashboard layout with clean typography
- Configurable API settings with fallback to mock data
- Multi-protocol support (MQTT, REST API, GraphQL, OPC UA)
- Multi-language support (English and Arabic)
- Enterprise and site management for multi-location deployments
- Subscription tiers with feature limitations
- Tank data source configuration for connecting tanks to cloud services

## Tech Stack
- **Backend**: Python, FastAPI, Pandas, NumPy, scikit-learn
- **Frontend**: React, Vite, Axios, Recharts, Material UI
- **Styling**: Modern CSS with CSS Variables, Grid Layout, and Flexbox
- **UI Design**: Custom-built component system with responsive design
- **Typography**: Google Fonts (Inter) for clean, modern text
- **Data Visualization**: Interactive charts with customized Recharts components
- **Data Storage**: JSON-based file storage (easily replaceable with a database)
- **Internationalization**: i18next for multi-language support
- **Protocol Support**: MQTT, REST API, GraphQL, OPC UA integrations
- **Authentication**: JWT-based authentication system

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

### Option 1: Using the Helper Script (Recommended)
```bash
# Make sure you're in the project root directory
# Run the backend server
python3 run_backend.py

# In a separate terminal, run the frontend server
cd frontend
npm run dev
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

### Troubleshooting
If you encounter issues with the backend server not starting properly:
1. Make sure all dependencies are installed in the virtual environment
2. Check that the `requests` package is installed: `pip install requests`
3. Use the helper script `run_backend.py` which handles virtual environment activation

If you see "Error fetching data: Network Error" in the frontend:
1. Ensure the backend server is running at http://localhost:8000
2. Check the backend server logs for any errors
3. Verify that the API configuration in the frontend is set to use http://localhost:8000

## API Endpoints

### Tank Data Endpoints
- `GET /api/tank-levels` - Get tank level readings (with optional filtering by days and tank ID)
- `POST /api/tank-levels` - Add a new tank level reading
- `GET /api/stats` - Get statistics about tank levels

### Anomaly Detection Endpoints
- `GET /api/anomalies` - Get detected anomalies in tank level data
- `POST /api/user-anomalies` - Report a missed anomaly
- `GET /api/user-anomalies` - Get user-reported anomalies
- `PUT /api/user-anomalies/{anomaly_id}` - Update anomaly status (admin only)
- `POST /api/mark-normal` - Mark a system-detected anomaly as normal (false positive)

### Subscription Endpoints
- `GET /api/subscription/tiers` - Get available subscription tiers
- `GET /api/subscription/current` - Get current user's subscription information

### Authentication Endpoints
- `POST /token` - Get authentication token
- `GET /users/me` - Get current user information

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

4. **User Feedback System**: The system includes a comprehensive feedback mechanism:
   - Users can report missed anomalies (false negatives)
   - Users can mark incorrectly identified anomalies as normal (false positives)
   - Administrators can review and confirm/reject user-reported anomalies
   - The system tracks model performance metrics based on user feedback

## Future Enhancements

1. **Database Integration**: Replace the JSON file storage with a proper database (PostgreSQL, MongoDB, etc.)
2. **Real-time Updates**: Implement WebSockets for real-time dashboard updates
3. **Advanced ML Models**: Implement more sophisticated anomaly detection algorithms
4. **Enhanced Mobile Support**: Optimize the mobile experience further
5. **Additional Protocols**: Add support for more industrial protocols (Modbus, BACnet, etc.)
6. **Notification System**: Implement email and SMS alerts for critical anomalies
7. **Advanced Analytics**: Add predictive maintenance and trend forecasting
8. **Custom Dashboards**: Allow users to create personalized dashboard layouts
9. **API Gateway**: Implement an API gateway for better security and rate limiting
10. **Containerization**: Provide Docker containers for easier deployment

## Version History

### v2.0.0 (Current)
- Added multi-protocol support (MQTT, REST API, GraphQL, OPC UA)
- Added tank data source configuration to connect tanks with cloud services
- Implemented comprehensive anomaly feedback system (report missed anomalies and mark false positives)
- Added enterprise and site management for multi-location deployments
- Added Arabic language support
- Fixed modal dialog usability issues
- Improved responsive design for large screens

### v1.0.0
- Initial release with core functionality
- Basic tank level monitoring
- Simple anomaly detection
- English-only interface
- Single-protocol support

## License
[MIT](https://choosealicense.com/licenses/mit/)
