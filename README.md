# Flood Monitoring System API & Dashboard

This project implements a comprehensive Flood Monitoring System featuring a FastAPI backend for data ingestion, processing, and API services, and a React frontend for visualization, user interaction, and real-time updates.

---

## Features

**Backend (FastAPI):**
* **User Authentication & Authorization:** JWT-based authentication with role-based access control (Admin, Commander, Field Responder, Government Official, Viewer).
* **Sensor Data Ingestion:** Endpoint for receiving sensor data (water level, rainfall, location).
* **Real-time Alerts:** Automatic alert generation based on sensor data thresholds (e.g., high water levels).
* **WebSocket Communication:**
    * Broadcasts new sensor data to connected clients.
    * Broadcasts new and resolved alerts.
    * Real-time chat functionality for authenticated users.
* **CRUD Operations:** For users, sensor data, alerts, and chat messages.
* **Spatial Analysis:**
    * Endpoints to retrieve sensors within a specified radius.
    * Data preparation for risk map visualization.
* **Database Integration:** Uses SQLAlchemy with PostgreSQL (configurable) for data persistence.
* **Modular Routers:** Organized API endpoints for alerts, chat, sensors, and spatial data.
* **CORS Configuration:** Allows frontend application to interact with the API.

**Frontend (React):**
* **User Login & Registration:** Secure user authentication flow.
* **Role-Based Dashboard:** Tailored dashboard views and functionalities based on user roles.
* **Live Map (Leaflet):**
    * Displays real-time sensor locations and status.
    * Updates dynamically via WebSocket sensor data.
* **Risk Map:**
    * Visualizes risk points based on sensor data.
    * Includes a heatmap layer for water level intensity.
    * Allows querying for sensors within a specified radius.
* **Alert Notifications:** Displays recent unresolved critical alerts and updates in real-time.
* **Live Chat:** Enables real-time communication between authenticated users.
* **Spatial Analysis Page:** Provides tools for querying sensor data (e.g., sensors in radius).
* **Protected Routes:** Ensures only authorized users can access specific pages and features.
* **Responsive Design:** Utilizes Bootstrap for styling.

---
```
flood-monitoring/
├── backend/app/          # Your FastAPI backend code
│           ├── init.py
│           ├── auth.py
│           ├── crud.py
│           ├── database.py
│           ├── main.py
│           ├── models.py
│           ├── schemas.py
│           ├── security.py
│           ├── websocket_manager.py
│           └── routers/
│               ├── init.py
│               ├── alert_router.py
│               ├── chat_router.py
│               ├── sensor_router.py
│               └── spatial_router.py
├── frontend/     # Your React frontend code
│   ├── public/
│   └── src/
│       ├── LiveMap.js
│       ├── reportWebVitals.js
│       ├── App.css
│       ├── index.js
│       ├── index.css
│       ├── App.test.js
│       ├── setupTests.js
│       ├── logo.svg
│       ├── services
│       │   ├── mapService.js
│       │   ├── chatService.js
│       │   ├── authService.js
│       │   └── alertService.js
│       ├── components
│       │   ├── Chat.css
│       │   ├── ProtectedRoute.js
│       │   ├── Chat.js
│       │   └── AlertNotifications.js
│       └── pages
│           ├── RiskMap.js
│           ├── SpatialAnalysisPage.js
│           ├── Dashboard.css
│           ├── Register.js
│           ├── Login.js
│           ├── Dashboard.js
│           └── Unauthorized.js
├── .env          # For environment variables
├── package.json
└── requirements.txt # For backend
```

## Tech Stack

**Backend:**

*   Python 3.7+
*   FastAPI
*   SQLAlchemy (with PostgreSQL)
*   Uvicorn (ASGI Server)
*   Passlib (for password hashing)
*   Python-JOSE (for JWT)
*   WebSockets

**Frontend:**

*   React 18+
*   React Router
*   Leaflet & React-Leaflet
*   React-Leaflet-Heatmap-Layer-v3
*   Axios (for HTTP requests)
*   Bootstrap
*   jwt-decode

## Setup and Installation

### Prerequisites

*   Python 3.7 or higher
*   Node.js (v16 or higher recommended) and npm (or yarn)
*   PostgreSQL Server (or another SQL database, with necessary adjustments to `DATABASE_URL` and `requirements.txt`)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-project-root>
```

### 2. Backend Setup

Create and Activate Python Virtual Environment:

```
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```


Install Backend Dependencies:

```
pip install -r requirements.txt
```

Configure Environment Variables:
Create a .env file in the project root by copying .env.example (if provided) or creating it manually:

```
# .env
DATABASE_URL="postgresql://your_db_user:your_db_password@your_db_host:your_db_port/your_db_name"
SECRET_KEY="your_very_strong_and_unique_secret_key"
ACCESS_TOKEN_EXPIRE_MINUTES=43200 # e.g., 30 days in minutes
```

Run the Backend Server:
The application will attempt to create database tables on startup if they don't exist.

```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
The API will be accessible at http://localhost:8000
API documentation (Swagger UI) will be at http://localhost:8000/docs.


### 3. Frontend Setup

Navigate to Frontend Directory:
Open a new terminal window/tab.
Install Frontend Dependencies:

```
npm install
# or if you use yarn:
# yarn install
```

Start the Frontend Development Server:

```
npm start
# or if you use yarn:
# yarn start
```

The frontend will typically be accessible at http://localhost:3000 and http://localhost:3001

```
Key endpoint groups:
/login: User login.
/register: User registration.
/users/me: Get current user details.
/alerts/: CRUD for alerts.
/chat/: Endpoints for fetching messages and WebSocket connection (/chat/ws).
/sensor-ingest: POST new sensor data.
/sensor-data: GET latest sensor data.
/spatial/: Endpoints for risk map data and querying sensors in a radius.
/ws/general: General WebSocket for sensor updates and alerts.
```
