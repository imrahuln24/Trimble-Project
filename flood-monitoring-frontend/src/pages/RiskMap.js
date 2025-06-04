// frontend/src/pages/RiskMap.js
import React, { useEffect, useState } from 'react'; // Removed useRef as it's not used
import { MapContainer, TileLayer, Popup, CircleMarker, LayersControl, FeatureGroup } from 'react-leaflet';
import { HeatmapLayer } from 'react-leaflet-heatmap-layer-v3';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchRiskMapData, fetchSensorsInRadius } from '../services/mapService';

// Leaflet marker icon fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
});

const RISK_COLOR = {
  low: 'green',
  medium: 'orange',
  high: 'red',
  unknown: 'grey'
};

const heatmapConfig = {
  radius: 25,
  maxOpacity: 0.8,
  scaleRadius: true,
  useLocalExtrema: false,
};

export default function RiskMap() {
  const [riskPoints, setRiskPoints] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]);
  const [queriedSensors, setQueriedSensors] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [mapComponentKey, setMapComponentKey] = useState(Date.now()); // For forcing map refresh

  const [queryLat, setQueryLat] = useState('');
  const [queryLon, setQueryLon] = useState('');
  const [queryRadius, setQueryRadius] = useState('10');
  const [queryWaterLevel, setQueryWaterLevel] = useState('');
  const [loadingQuery, setLoadingQuery] = useState(false);


  useEffect(() => {
    setLoading(true);
    setError(''); // Clear previous errors
    console.log("RiskMap: Fetching risk map data...");
    fetchRiskMapData()
      .then(res => {
        console.log("RiskMap: Data received for risk points", res.data);
        if (!Array.isArray(res.data)) {
            throw new Error("Risk map data is not an array");
        }
        setRiskPoints(res.data);
        const hmData = res.data
          .filter(p => p.latitude != null && p.longitude != null && p.water_level != null)
          .map(p => [p.latitude, p.longitude, parseFloat(p.water_level) || 0]);
        console.log("RiskMap: Heatmap data prepared:", hmData);
        setHeatmapData(hmData);
        setMapComponentKey(Date.now()); // Update key to potentially help refresh map if needed
      })
      .catch(err => {
        console.error("RiskMap: Failed to load risk map data:", err);
        setError("Failed to load risk map data. " + (err.response?.data?.detail || err.message || String(err)));
      })
      .finally(() => {
        console.log("RiskMap: Fetch complete, setting loading to false.");
        setLoading(false);
      });
  }, []);

  const handleSpatialQuery = (e) => {
    e.preventDefault();
    if (!queryLat || !queryLon || !queryRadius) {
      alert("Please provide Latitude, Longitude, and Radius for the query.");
      return;
    }
    setLoadingQuery(true); // Use separate loading state for query
    setError(''); // Clear general error for new query
    setQueriedSensors([]); // Clear previous query results

    fetchSensorsInRadius(
      parseFloat(queryLat),
      parseFloat(queryLon),
      parseFloat(queryRadius),
      queryWaterLevel ? parseFloat(queryWaterLevel) : null
    )
      .then(res => {
        console.log("RiskMap: Queried sensors received", res.data);
        if (!Array.isArray(res.data)) {
            throw new Error("Queried sensor data is not an array");
        }
        setQueriedSensors(res.data);
        if (res.data.length === 0) alert("No sensors found matching your criteria.");
      })
      .catch(err => {
        console.error("RiskMap: Spatial query error:", err);
        setError("Spatial query failed. " + (err.response?.data?.detail || err.message || String(err)));
      })
      .finally(() => setLoadingQuery(false));
  };

  const mapCenter = [13.0827, 80.2707]; // Default to Chennai

  if (loading && riskPoints.length === 0 && !error) {
    return <div className="container mt-5 text-center"><p>Loading risk map...</p></div>;
  }

  // Show error prominently if data fetching fails
  if (error && riskPoints.length === 0) { // Only show if critical data (riskPoints) failed
    return <div className="alert alert-danger m-3 p-3"><strong>Error:</strong> {error}</div>;
  }
  
  // If no error, but also no risk points after loading, it might be an empty dataset
  if (!loading && riskPoints.length === 0 && !error) {
    return <div className="alert alert-info m-3 p-3">No risk point data available to display on the map.</div>;
  }


  return (
    <div className="d-flex flex-column" style={{ height: 'calc(100vh - 56px)', width: '100%' }}> {/* Adjust height if you have a navbar */}
      {/* Spatial Query Form - RESTORED */}
      <div className="p-2 bg-light border-bottom">
        <form onSubmit={handleSpatialQuery} className="row gx-2 gy-2 align-items-center">
          <div className="col-auto"><label className="form-label-sm fw-bold">Find Sensors Near:</label></div>
          <div className="col-md-2 col-sm-4">
            <input type="number" step="any" className="form-control form-control-sm" placeholder="Latitude" value={queryLat} onChange={e => setQueryLat(e.target.value)} required />
          </div>
          <div className="col-md-2 col-sm-4">
            <input type="number" step="any" className="form-control form-control-sm" placeholder="Longitude" value={queryLon} onChange={e => setQueryLon(e.target.value)} required />
          </div>
          <div className="col-md-2 col-sm-4">
            <input type="number" step="any" className="form-control form-control-sm" placeholder="Radius (km)" value={queryRadius} onChange={e => setQueryRadius(e.target.value)} required />
          </div>
          <div className="col-md-3 col-sm-6">
            <input type="number" step="any" className="form-control form-control-sm" placeholder="Min Water Level (m, optional)" value={queryWaterLevel} onChange={e => setQueryWaterLevel(e.target.value)} />
          </div>
          <div className="col-auto">
            <button type="submit" className="btn btn-primary btn-sm" disabled={loadingQuery}>
              {loadingQuery ? 'Querying...' : 'Query Sensors'}
            </button>
          </div>
        </form>
        {/* Display query-specific error, not the general page error */}
        {error && loadingQuery === false && queriedSensors.length === 0 && <div className="text-danger small mt-1 ms-1">{error.includes("Spatial query failed") ? error : ""}</div>}
      </div>

      {/* Map Area */}
      <div style={{ flexGrow: 1, border: '1px solid #ccc' }}>
        {(riskPoints.length > 0 || queriedSensors.length > 0) ? ( // Only render map if there's some data to show or query results
          <MapContainer key={mapComponentKey} center={mapCenter} zoom={7} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <LayersControl position="topright">
              <LayersControl.Overlay checked name="Risk Points">
                <FeatureGroup>
                  {riskPoints.map((point) => (
                    (point.latitude != null && point.longitude != null) &&
                    <CircleMarker
                      key={`risk-${point.sensor_id || Math.random()}`} // Use sensor_id if available
                      center={[point.latitude, point.longitude]}
                      radius={8}
                      pathOptions={{
                        color: RISK_COLOR[String(point.risk_level).toLowerCase()] || RISK_COLOR.unknown,
                        fillColor: RISK_COLOR[String(point.risk_level).toLowerCase()] || RISK_COLOR.unknown,
                        fillOpacity: 0.6
                      }}
                    >
                      <Popup>
                        <div>
                          <strong>Sensor ID:</strong> {point.sensor_id || "N/A"}<br />
                          <strong>Risk:</strong> {String(point.risk_level).toUpperCase() || "UNKNOWN"} <br />
                          {point.water_level !== null && <><strong>Water Level:</strong> {point.water_level.toFixed(2)} m <br /></>}
                          <small>Last Updated: {point.last_updated ? new Date(point.last_updated).toLocaleString() : 'N/A'}</small>
                        </div>
                      </Popup>
                    </CircleMarker>
                  ))}
                </FeatureGroup>
              </LayersControl.Overlay>

              <LayersControl.Overlay checked name="Water Level Heatmap">
                {heatmapData.length > 0 && (
                  <HeatmapLayer
                    points={heatmapData}
                    longitudeExtractor={m => m[1]}
                    latitudeExtractor={m => m[0]}
                    intensityExtractor={m => m[2]}
                    {...heatmapConfig}
                  />
                )}
              </LayersControl.Overlay>

              {queriedSensors.length > 0 && (
                <LayersControl.Overlay checked name="Queried Sensors">
                  <FeatureGroup>
                    {queriedSensors.map(sensor => (
                      (sensor.latitude != null && sensor.longitude != null) &&
                      <CircleMarker
                        key={`query-${sensor.id || sensor.sensor_id}`}
                        center={[sensor.latitude, sensor.longitude]}
                        radius={10}
                        pathOptions={{ color: 'purple', fillColor: '#800080', fillOpacity: 0.7 }}
                      >
                        <Popup>
                          <div>
                            <strong>Queried Sensor ID:</strong> {sensor.sensor_id} <br />
                            <strong>Water Level:</strong> {sensor.water_level?.toFixed(2)} m <br />
                            <strong>Rainfall:</strong> {sensor.rainfall?.toFixed(1)} mm <br />
                            <strong>Timestamp:</strong> {sensor.timestamp ? new Date(sensor.timestamp).toLocaleString() : 'N/A'}
                          </div>
                        </Popup>
                      </CircleMarker>
                    ))}
                  </FeatureGroup>
                </LayersControl.Overlay>
              )}
            </LayersControl>
          </MapContainer>
        ) : (
             <div className="p-5 text-center text-muted">
                {loading ? "Loading map data..." : "No data to display on the map."}
             </div>
        )}
      </div>
    </div>
  );
}

/*
import React, { useEffect, useState} from 'react';
import { MapContainer, TileLayer, Popup, CircleMarker, LayersControl, FeatureGroup } from 'react-leaflet';
import { HeatmapLayer } from 'react-leaflet-heatmap-layer-v3';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchRiskMapData, fetchSensorsInRadius } from '../services/mapService'; // New service

// Leaflet marker icon fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
});

const RISK_COLOR = {
  low: 'green',
  medium: 'orange',
  high: 'red',
  unknown: 'grey'
};

const heatmapConfig = {
  radius: 20, // Adjusted for potentially denser data from arrays
  maxOpacity: 0.8,
  scaleRadius: true,
  useLocalExtrema: false,
  // valueField: 'intensity', // Not needed for array format [lat, lng, intensity]
  // latField: 'lat',         // Not needed for array format
  // lngField: 'lng',         // Not needed for array format
};


function RiskMap() {
  const [riskPoints, setRiskPoints] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]); // Data specifically for heatmap layer // Data specifically for heatmap layer
  const [queriedSensors, setQueriedSensors] = useState([]); // For spatial query results
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  // Spatial Query Form State
  const [queryLat, setQueryLat] = useState('');
  const [queryLon, setQueryLon] = useState('');
  const [queryRadius, setQueryRadius] = useState('10'); // Default 10 km
  const [queryWaterLevel, setQueryWaterLevel] = useState('');


  useEffect(() => {
    setLoading(true);
    console.log("RiskMap: Fetching risk map data...");
    fetchRiskMapData()
      .then(res => {
        console.log("RiskMap: Data received", res.data);
        setRiskPoints(res.data);
        // Prepare data for heatmap: array of [lat, lng, intensity]
        const hmData = res.data
          .filter(p => p.latitude != null && p.longitude != null && p.water_level != null) // Ensure all are present
          .map(p => [p.latitude, p.longitude, parseFloat(p.water_level) || 0]); // Using water_level as intensity
        
        console.log("Heatmap data prepared:", hmData); // Check the structure
        setHeatmapData(hmData);
        setError('');
      })
      .catch(err => {
        console.error("RiskMap: Failed to load risk map data:", err);
        console.error("Risk map data error:", err);
        setError("Failed to load risk map data. " + (err.response?.data?.detail || err.message));
      })
      .finally(() => {
      console.log("RiskMap: Fetch complete, setting loading to false.");
      setLoading(false)
    });
  }, []);

  const handleSpatialQuery = (e) => {
    e.preventDefault();
    if (!queryLat || !queryLon || !queryRadius) {
        alert("Please provide Latitude, Longitude, and Radius for the query.");
        return;
    }
    setLoading(true);
    fetchSensorsInRadius(
        parseFloat(queryLat), 
        parseFloat(queryLon), 
        parseFloat(queryRadius),
        queryWaterLevel ? parseFloat(queryWaterLevel) : null
    )
    .then(res => {
        setQueriedSensors(res.data);
        setError('');
        if (res.data.length === 0) alert("No sensors found matching your criteria.");
    })
    .catch(err => {
        console.error("Spatial query error:", err);
        setError("Spatial query failed. " + (err.response?.data?.detail || err.message));
        setQueriedSensors([]);
    })
    .finally(() => setLoading(false));
  };


  if (loading && riskPoints.length === 0) { // Show loading only on initial load
    return <div className="container mt-5 text-center"><p>Loading risk map...</p></div>;
  }

  if (error && riskPoints.length === 0) {
    return <div className="alert alert-danger m-3">{error}</div>;
  }

  const mapCenter = [13.0827, 80.2707]; // Default to Chennai

  return (
    <div style={{ flexGrow: 1 }}>
      <MapContainer center={mapCenter} zoom={7} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LayersControl position="topright">
        
            <LayersControl.Overlay checked name="Risk Points">
              <FeatureGroup>
                {riskPoints.map((point, idx) => (
                  (point.latitude != null && point.longitude != null) && // Check for valid lat/lng
                  <CircleMarker
                    key={`risk-${idx}-${point.sensor_id || 'unk'}`}
                    center={[point.latitude, point.longitude]}
                    radius={8}
                    pathOptions={{ 
                        color: RISK_COLOR[point.risk_level.toLowerCase()] || 'grey', 
                        fillColor: RISK_COLOR[point.risk_level.toLowerCase()] || 'grey',
                        fillOpacity: 0.6 
                    }}
                  >
                    <Popup>
                      <div>
                        <strong>Sensor ID:</strong> {point.sensor_id || "N/A"}<br />
                        <strong>Risk:</strong> {point.risk_level ? point.risk_level.toUpperCase() : "UNKNOWN"} <br />
                        {point.water_level !== null && <><strong>Water Level:</strong> {point.water_level.toFixed(2)} m <br /></>}
                        <small>Last Updated: {point.last_updated ? new Date(point.last_updated).toLocaleString() : (point.timestamp ? new Date(point.timestamp).toLocaleString() : 'N/A')}</small>
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </FeatureGroup>
            </LayersControl.Overlay>


          <LayersControl.Overlay checked name="Water Level Heatmap">
          
            {heatmapData.length > 0 ? (
              <HeatmapLayer 
                points={heatmapData} 
                longitudeExtractor={m => m[1]} // For [lat, lng, intensity] format
                latitudeExtractor={m => m[0]}  // For [lat, lng, intensity] format
                intensityExtractor={m => m[2]} // For [lat, lng, intensity] format
                {...heatmapConfig} 
              />
            ) : (
              <FeatureGroup>
               
              </FeatureGroup>
            )}
          </LayersControl.Overlay>
          
        
             {queriedSensors.length > 0 && (
                <LayersControl.Overlay checked name="Queried Sensors">
                    <FeatureGroup>
                        {queriedSensors.map(sensor => (
                             (sensor.latitude != null && sensor.longitude != null) && // Check lat/lng
                             <CircleMarker
                                key={`query-${sensor.id || sensor.sensor_id}`}
                                center={[sensor.latitude, sensor.longitude]}
                                radius={10} 
                                pathOptions={{ color: 'purple', fillColor: '#800080', fillOpacity: 0.7 }}
                              >
                                <Popup>
                                  <div>
                                    <strong>Queried Sensor ID:</strong> {sensor.sensor_id} <br />
                                    <strong>Water Level:</strong> {sensor.water_level?.toFixed(2)} m <br />
                                    <strong>Rainfall:</strong> {sensor.rainfall?.toFixed(1)} mm <br />
                                    <strong>Timestamp:</strong> {sensor.timestamp ? new Date(sensor.timestamp).toLocaleString() : 'N/A'}
                                  </div>
                                </Popup>
                            </CircleMarker>
                        ))}
                    </FeatureGroup>
                </LayersControl.Overlay>
            )}
        </LayersControl>
      </MapContainer>
    </div>
);
}

export default RiskMap;


import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Circle, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Leaflet marker icon fix for bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon-2x.png',
  iconUrl:
    'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png',
  shadowUrl:
    'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png',
});

const RISK_COLOR = {
  low: 'green',
  medium: 'orange',
  high: 'red'
};

function RiskMap() {
  const [riskData, setRiskData] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/risk-map", {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`
      }
    })
      .then(res => {
        if (!res.ok) throw new Error("Unauthorized or failed to fetch risk map");
        return res.json();
      })
      .then(data => setRiskData(data))
      .catch(error => console.error("Risk map error:", error));
  }, []);

  return (
    <div style={{ height: '100vh', width: '100%' }}>
      <MapContainer center={[20, 77]} zoom={6} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        />
        {riskData.map((point, idx) => (
          <Circle
            key={idx}
            center={[point.latitude, point.longitude]}
            radius={3000}
            pathOptions={{ color: RISK_COLOR[point.risk], fillOpacity: 0.5 }}
          >
            <Popup>
              <div>
                <strong>Risk:</strong> {point.risk.toUpperCase()} <br />
                <strong>Water Level:</strong> {point.water_level.toFixed(2)} m <br />
                <strong>Rainfall:</strong> {point.rainfall.toFixed(1)} mm
              </div>
            </Popup>
          </Circle>
        ))}
      </MapContainer>
    </div>
  );
}

export default RiskMap;
*/