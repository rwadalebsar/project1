# Tank Level Monitoring Dashboard

## Description
A comprehensive dashboard for monitoring tank level sensors with data visualization, API integration, and machine learning for anomaly detection. This project demonstrates how to create a full-stack application with a Python backend and React frontend.

## Features
- RESTful API built with FastAPI
- Multi-protocol support for external data sources:
  - MQTT protocol with multiple connection support
  - REST API protocol with multiple connection support
  - GraphQL protocol with multiple connection support
  - OPC UA protocol with multiple connection support
- Tank-to-connection mapping for flexible data source configuration
- Interactive charts for visualizing tank level data
- Historical data tracking for up to 12 months
- Detailed views for recent data (3 days)
- Machine learning-based anomaly detection with user feedback system
- Modern UI with responsive design for all device sizes
- Dark mode sidebar with intuitive navigation
- Card-based dashboard layout with clean typography
- Configurable API settings with fallback to mock data
- Multi-language support (English and Arabic)
- Enterprise and site management for multi-location deployments

## Tech Stack
- **Backend**: Python, FastAPI, Pandas, NumPy, scikit-learn
- **Frontend**: React, Vite, Axios, Recharts
- **Styling**: Modern CSS with CSS Variables, Grid Layout, and Flexbox
- **UI Design**: Custom-built component system with responsive design
- **Typography**: Google Fonts (Inter) for clean, modern text
- **Data Visualization**: Interactive charts with customized Recharts components
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

- `GET /api/tank-levels` - Get tank level readings (with optional filtering by days and tank ID)
- `POST /api/tank-levels` - Add a new tank level reading
- `GET /api/anomalies` - Get detected anomalies in tank level data
- `POST /api/anomalies/mark-normal` - Mark an anomaly as normal to improve the model
- `POST /api/user-anomalies` - Report a missed anomaly
- `GET /api/stats` - Get statistics about tank levels

## External Data Source Integration

The application is designed to work with various external tank level sensor data sources through multiple protocols. It includes:

1. **Multi-Protocol Support**: The system supports four different protocols for connecting to external data sources:
   - **MQTT**: Connect to MQTT brokers with support for multiple simultaneous connections
   - **REST API**: Connect to RESTful APIs with support for multiple simultaneous connections
   - **GraphQL**: Connect to GraphQL endpoints with support for multiple simultaneous connections
   - **OPC UA**: Connect to OPC UA servers with support for multiple simultaneous connections

2. **Configurable Connection Settings**: Each protocol has its own configuration panel where you can set:
   - Connection details (URL/endpoint, port, credentials, etc.)
   - Authentication settings (API keys, username/password, etc.)
   - Protocol-specific options
   - Tank-to-connection mapping for flexible data routing

3. **Connection Management**: The system provides a user-friendly interface for:
   - Adding new connections
   - Editing existing connections
   - Deleting connections
   - Testing connection status
   - Monitoring data flow

4. **Fallback Mechanism**: If external data sources are unavailable, the system falls back to cached data or generates mock data.

5. **Service Layer**: The backend includes a dedicated service layer that handles:
   - Authentication for various protocols
   - Data fetching and caching
   - Error handling
   - Protocol-specific communication
   - Mock data generation for development and testing

6. **Configuration Storage**: Connection settings are stored securely and can be managed through the user interface.

## Machine Learning Implementation

The system uses the Isolation Forest algorithm from scikit-learn for anomaly detection. This algorithm is particularly well-suited for detecting outliers in time series data:

1. **How it works**: Isolation Forest isolates observations by randomly selecting a feature and then randomly selecting a split value between the maximum and minimum values of the selected feature.
2. **Advantages**:
   - Efficient with high-dimensional datasets
   - Requires minimal configuration (primarily the contamination parameter)
   - Works well with time series data
   - Doesn't make assumptions about the data distribution

3. **Implementation**: The backend processes tank level readings and identifies unusual patterns that might indicate sensor malfunctions, leaks, or other issues.

4. **User Feedback System**: The system incorporates a feedback mechanism that allows users to:
   - Mark false positive anomalies as normal
   - Report missed anomalies that the system didn't detect
   - Improve the model's accuracy over time through continuous learning

5. **Adaptive Learning**: The anomaly detection model adapts based on user feedback:
   - Readings marked as normal are excluded from future anomaly detection
   - The system learns patterns of normal behavior specific to each tank
   - False positive reduction improves alert quality and reduces alert fatigue

## Deployment

The application can be deployed to Google Cloud Run for a scalable, containerized deployment. For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deployment Steps

1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Run the deployment script: `./deploy-to-cloud-run.sh`
3. Access your application at the provided URLs

### Docker Support

The application includes Docker configuration for both local development and production deployment:

```bash
# Run locally with Docker Compose
docker-compose up --build
```

## Future Enhancements

1. **Database Integration**: Replace the JSON file storage with a proper database (PostgreSQL, MongoDB, etc.)
2. **Real-time Updates**: Implement WebSockets for real-time dashboard updates
3. **Advanced ML Models**: Implement more sophisticated anomaly detection algorithms
4. **Enhanced User Management**: Add role-based access control and user permissions
5. **Mobile App**: Develop a companion mobile application for on-the-go monitoring
6. **Additional Protocols**: Add support for more industrial protocols (Modbus, BACnet, etc.)
7. **Advanced Analytics**: Implement predictive maintenance and trend analysis
8. **Reporting System**: Add customizable reports and scheduled exports
9. **CI/CD Pipeline**: Set up continuous integration and deployment for automated testing and deployment

## Version History

### v3.1.0 (Current)
- Added "Mark as Normal" feature for anomaly detection feedback
- Improved machine learning model to incorporate user feedback
- Enhanced anomaly detection accuracy by learning from user corrections
- Fixed UI issues with button rendering and styling

### v3.0.0
- Added multiple connection support for all protocols (MQTT, REST API, GraphQL, OPC UA)
- Implemented tank-to-connection mapping for flexible data routing
- Enhanced UI for connection management
- Improved protocol configuration interfaces

### v2.0.0
- Added multi-protocol support (MQTT, REST API, GraphQL, OPC UA)
- Implemented tank data source configuration
- Added anomaly feedback system for ML model improvement
- Enhanced dashboard with better data visualization

### v1.2.0
- Fixed navigation issues
- Improved subscription page
- Added multi-protocol support information to login features

### v1.1.0
- Fixed user authentication
- Added standalone registration page
- Fixed sidebar menu labels

### v1.0.0
- Initial release with basic tank monitoring functionality
- Dashboard with tank level visualization
- Anomaly detection system
- API integration

## License
[MIT](https://choosealicense.com/licenses/mit/)
