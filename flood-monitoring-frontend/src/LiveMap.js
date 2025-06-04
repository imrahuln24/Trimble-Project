// frontend/src/LiveMap.js
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
// import 'bootstrap/dist/css/bootstrap.min.css'; // Usually not needed directly in component if imported globally

// Leaflet marker icon fix (keep this)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
});

const SENSOR_MARKER_COLORS = {
    high: 'red',    // water_level > 7
    medium: 'orange',// water_level > 4 (or 5 depending on your logic)
    low: 'blue',   // default
    default: '#777' // For null or undefined water levels
};

function getSensorColor(waterLevel) {
    if (waterLevel == null) return SENSOR_MARKER_COLORS.default;
    if (waterLevel > 7.0) return SENSOR_MARKER_COLORS.high;
    if (waterLevel > 4.0) return SENSOR_MARKER_COLORS.medium; // Adjust if your threshold is 5.0
    return SENSOR_MARKER_COLORS.low;
}


export default function LiveMap({ sensorUpdateFromWebSocket }) {
  const [sensorData, setSensorData] = useState([]);
  const [error, setError] = useState('');
  const mapRef = useRef();

  const fetchInitialData = useCallback(() => {
    console.log("LiveMap: Fetching initial sensor data from /sensor-data...");
    // Assuming /sensor-data is available at the root of your API
    // This endpoint is now defined in sensor_router.py without a prefix
    fetch('http://127.0.0.1:8000/sensor-data?limit=50')
      .then(res => {
        if (!res.ok) {
            // Try to parse error from backend if JSON
            return res.json().then(errData => {
                throw new Error(`HTTP error! status: ${res.status}, detail: ${errData.detail || JSON.stringify(errData)}`);
            }).catch(() => { // If error response is not JSON
                throw new Error(`HTTP error! status: ${res.status}, statusText: ${res.statusText}`);
            });
        }
        return res.json();
      })
      .then(data => {
        console.log("LiveMap: Initial sensor data received:", data);
        setSensorData(data);
        setError('');
      })
      .catch(err => {
        console.error("LiveMap: Failed to fetch initial sensor data:", err);
        setError(`Could not load sensor data: ${err.message}`);
      });
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  useEffect(() => {
    if (sensorUpdateFromWebSocket) {
      console.log("LiveMap: Received sensor update via WebSocket:", sensorUpdateFromWebSocket);
      setSensorData(prevData => {
        const existingIndex = prevData.findIndex(s => s.id === sensorUpdateFromWebSocket.id);
        let newDataArray;
        if (existingIndex !== -1) {
          newDataArray = [...prevData];
          newDataArray[existingIndex] = sensorUpdateFromWebSocket;
        } else {
          newDataArray = [sensorUpdateFromWebSocket, ...prevData];
        }
        return newDataArray.slice(0, 100); // Keep most recent 100
      });
    }
  }, [sensorUpdateFromWebSocket]);

  if (error) {
    return <div className="alert alert-warning text-center p-3 m-2">{error}</div>;
  }

  // Default center, can be adjusted or made dynamic
  const mapCenter = sensorData.length > 0 && sensorData[0].latitude && sensorData[0].longitude
    ? [sensorData[0].latitude, sensorData[0].longitude]
    : [13.0827, 80.2707]; // Default to Chennai

  if (sensorData.length === 0 && !error) {
      return <div className="p-3 text-center">Loading sensor data for map...</div>;
  }

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <MapContainer
        key={JSON.stringify(mapCenter)} // Force re-render if center changes significantly, optional
        center={mapCenter}
        zoom={7}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef} // Use whenCreated prop for map instance if needed for direct Leaflet API calls
      >
        <TileLayer
          attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        />

        {sensorData.map(sensor => (
          (typeof sensor.latitude === 'number' && typeof sensor.longitude === 'number') && (
            <CircleMarker
              key={sensor.id || sensor.sensor_id} // Ensure unique key
              center={[sensor.latitude, sensor.longitude]}
              radius={8}
              pathOptions={{
                color: getSensorColor(sensor.water_level),
                fillColor: getSensorColor(sensor.water_level),
                fillOpacity: 0.7
              }}
            >
              <Popup>
                <div>
                  <strong>Sensor ID:</strong> {sensor.sensor_id} <br />
                  <strong>Water Level:</strong> {sensor.water_level != null ? sensor.water_level.toFixed(2) + ' m' : 'N/A'} <br />
                  <strong>Rainfall:</strong> {sensor.rainfall != null ? sensor.rainfall.toFixed(1) + ' mm' : 'N/A'} <br />
                  <strong>Timestamp:</strong> {new Date(sensor.timestamp).toLocaleString()}
                </div>
              </Popup>
            </CircleMarker>
          )
        ))}
      </MapContainer>
    </div>
  );
}
/*

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'bootstrap/dist/css/bootstrap.min.css';

// Leaflet marker icon fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
});

function LiveMap({ sensorUpdateFromWebSocket }) { // Accept prop
  const [sensorData, setSensorData] = useState([]);
  const [error, setError] = useState('');
  // No WebSocket directly in LiveMap anymore, it's handled by Dashboard

  const mapRef = useRef(); // For potential map interactions later

  // Initial fetch for sensor data
  const fetchInitialData = useCallback(() => {
    fetch('http://127.0.0.1:8000/sensor-data?limit=50') // Fetch a reasonable initial amount
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        setSensorData(data);
        setError('');
      })
      .catch(err => {
        console.error("Failed to fetch initial sensor data:", err);
        setError("Could not load sensor data.");
      });
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  // Handle WebSocket updates passed via prop
  useEffect(() => {
    if (sensorUpdateFromWebSocket) {
      setSensorData(prevData => {
        // Update existing sensor or add new one
        const existingIndex = prevData.findIndex(s => s.id === sensorUpdateFromWebSocket.id);
        let newDataArray;
        if (existingIndex !== -1) {
          newDataArray = [...prevData];
          newDataArray[existingIndex] = sensorUpdateFromWebSocket;
        } else {
          // Add new sensor to the beginning and limit array size
          newDataArray = [sensorUpdateFromWebSocket, ...prevData];
        }
        return newDataArray.slice(0, 100); // Keep most recent 100
      });
    }
  }, [sensorUpdateFromWebSocket]);

  if (error) {
    return <div className="alert alert-warning text-center">{error}</div>;
  }
  
  const mapCenter = [13.0827, 80.2707]; // Default to Chennai or a central point
  // const mapCenter = sensorData.length > 0 && sensorData[0].latitude && sensorData[0].longitude
  //   ? [sensorData[0].latitude, sensorData[0].longitude]
  //   : [20.5937, 78.9629]; // India center if no data

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <MapContainer 
        center={mapCenter} 
        zoom={7} // Adjust zoom level
        style={{ height: '100%', width: '100%' }}
        whenCreated={mapInstance => { mapRef.current = mapInstance; }}
      >
        <TileLayer
          attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        />

        {sensorData.map(sensor => (
          (typeof sensor.latitude === 'number' && typeof sensor.longitude === 'number') && (
            <CircleMarker
              key={sensor.id}
              center={[sensor.latitude, sensor.longitude]}
              radius={8} // Slightly smaller radius
              pathOptions={{ // Use pathOptions for CircleMarker
                color: sensor.water_level > 7 ? 'red' : (sensor.water_level > 4 ? 'orange' : 'blue'),
                fillColor: sensor.water_level > 7 ? '#f03' : (sensor.water_level > 4 ? '#f90' : '#39f'),
                fillOpacity: 0.6
              }}
            >
              <Popup>
                <div>
                  <strong>Sensor ID:</strong> {sensor.sensor_id} <br />
                  <strong>Water Level:</strong> {sensor.water_level?.toFixed(2)} m <br />
                  <strong>Rainfall:</strong> {sensor.rainfall?.toFixed(1)} mm <br />
                  <strong>Timestamp:</strong> {new Date(sensor.timestamp).toLocaleString()}
                </div>
              </Popup>
            </CircleMarker>
          )
        ))}
      </MapContainer>
    </div>
  );
}

export default LiveMap;

import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';


delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon-2x.png',
  iconUrl:
    'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
});

function LiveMap() {
  const [sensorData, setSensorData] = useState([]);
  const ws = useRef(null);

  // Initial fetch
  useEffect(() => {
    fetch('http://127.0.0.1:8000/sensor-data')
      .then(res => res.json())
      .then(data => setSensorData(data));
  }, []);

  // WebSocket for live updates
  useEffect(() => {
    ws.current = new WebSocket('ws://127.0.0.1:8000/ws/sensor');

    ws.current.onmessage = (event) => {
      const newData = JSON.parse(event.data);
      setSensorData(prev => [newData, ...prev].slice(0, 100));  // Keep most recent 100
    };

    ws.current.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === "sensor") {
    setSensorData(prev => [message.data, ...prev].slice(0, 100));
  } else if (message.type === "alert") {
    // Show notification or update alert list
    // You could add a state to store live alerts and show toast/popups
    alert(`ALERT: ${message.alert.title} - ${message.alert.description}`);
    
  }
};


    return () => {
      ws.current.close();
    };
  }, []);

  

  return (
    <div style={{ height: '100vh', width: '100%' }}>
      <MapContainer center={[20, 77]} zoom={6} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        />

        {sensorData.map(sensor => (
          sensor.latitude !== undefined &&
  sensor.longitude !== undefined && <CircleMarker
            key={sensor.id}
            center={[sensor.latitude, sensor.longitude]}
            radius={10}
            color={sensor.water_level > 7 ? 'red' : 'blue'}
            fillOpacity={0.5}
          >
            <Popup>
              <div>
                <strong>Sensor ID:</strong> {sensor.sensor_id} <br />
                <strong>Water Level:</strong> {sensor.water_level} m <br />
                <strong>Rainfall:</strong> {sensor.rainfall} mm <br />
                <strong>Timestamp:</strong> {new Date(sensor.timestamp).toLocaleString()}
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );

  
}

export default LiveMap;






import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import L from 'leaflet';

// Fix default marker icon issue in Leaflet with React
delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon-2x.png',
  iconUrl:
    'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
});

function App() {
  const [sensorData, setSensorData] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/sensor-data')
      .then(res => res.json())
      .then(data => setSensorData(data))
      .catch(console.error);
  }, []);

  return (
    <div style={{ height: '100vh', width: '100%' }}>
      <MapContainer center={[20, 77]} zoom={6} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        />

        {sensorData.map(sensor => (
          <CircleMarker
            key={sensor.id}
            center={[sensor.latitude, sensor.longitude]}
            radius={10}
            color={sensor.water_level > 7 ? 'red' : 'blue'}
            fillOpacity={0.5}
          >
            <Popup>
              <div>
                <strong>Sensor ID:</strong> {sensor.sensor_id} <br />
                <strong>Water Level:</strong> {sensor.water_level} m <br />
                <strong>Rainfall:</strong> {sensor.rainfall} mm <br />
                <strong>Timestamp:</strong> {new Date(sensor.timestamp).toLocaleString()}
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}

export default App;



import logo from './logo.svg';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;
*/