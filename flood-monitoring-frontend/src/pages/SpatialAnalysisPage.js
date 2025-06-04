// frontend/src/pages/SpatialAnalysisPage.js
import React, { useState } from 'react'; // Removed useEffect, etc. if only form is needed
import { fetchSensorsInRadius } from '../services/mapService'; // Assuming you'll display results or map them
// If you add a map here, you'll need MapContainer, TileLayer, etc.

export default function SpatialAnalysisPage() {
  // State for the query form (copied from RiskMap.js)
  const [queryLat, setQueryLat] = useState('');
  const [queryLon, setQueryLon] = useState('');
  const [queryRadius, setQueryRadius] = useState('10');
  const [queryWaterLevel, setQueryWaterLevel] = useState('');
  const [queriedSensors, setQueriedSensors] = useState([]);
  const [loadingQuery, setLoadingQuery] = useState(false);
  const [queryError, setQueryError] = useState('');

  const handleSpatialQuery = (e) => {
    e.preventDefault();
    if (!queryLat || !queryLon || !queryRadius) {
        alert("Please provide Latitude, Longitude, and Radius for the query.");
        return;
    }
    setLoadingQuery(true);
    setQueryError('');
    setQueriedSensors([]); // Clear previous results

    fetchSensorsInRadius(
        parseFloat(queryLat), 
        parseFloat(queryLon), 
        parseFloat(queryRadius),
        queryWaterLevel ? parseFloat(queryWaterLevel) : null
    )
    .then(res => {
        setQueriedSensors(res.data);
        if (res.data.length === 0) alert("No sensors found matching your criteria.");
    })
    .catch(err => {
        console.error("Spatial query error:", err);
        setQueryError("Spatial query failed. " + (err.response?.data?.detail || err.message));
    })
    .finally(() => setLoadingQuery(false));
  };

  return (
    <div className="container mt-5">
      <div className="card">
        <div className="card-header">
          <h2>Spatial Analysis Tools</h2>
        </div>
        <div className="card-body">
          <p>This page will contain advanced spatial analysis tools and queries.</p>
          
          <h4 className="mt-4">Find Sensors in Radius</h4>
          {/* Spatial Query Form (copied and adapted from RiskMap.js) */}
          <div className="p-2 bg-light border rounded mb-3">
            <form onSubmit={handleSpatialQuery} className="row gx-2 gy-2 align-items-center">
              <div className="col-auto"><label className="form-label-sm">Center Point:</label></div>
              <div className="col-md-2">
                <input type="number" step="any" className="form-control form-control-sm" placeholder="Latitude" value={queryLat} onChange={e => setQueryLat(e.target.value)} required />
              </div>
              <div className="col-md-2">
                <input type="number" step="any" className="form-control form-control-sm" placeholder="Longitude" value={queryLon} onChange={e => setQueryLon(e.target.value)} required />
              </div>
              <div className="col-md-2">
                <input type="number" step="any" className="form-control form-control-sm" placeholder="Radius (km)" value={queryRadius} onChange={e => setQueryRadius(e.target.value)} required />
              </div>
              <div className="col-md-2">
                <input type="number" step="any" className="form-control form-control-sm" placeholder="Min Water (m, optional)" value={queryWaterLevel} onChange={e => setQueryWaterLevel(e.target.value)} />
              </div>
              <div className="col-auto">
                <button type="submit" className="btn btn-primary btn-sm" disabled={loadingQuery}>Query Sensors</button>
              </div>
              {loadingQuery && <div className="col-auto"><span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span></div>}
            </form>
            {queryError && !loadingQuery && <div className="text-danger small mt-1 ms-1">{queryError}</div>}
          </div>

          {/* Display Queried Sensors */}
          {queriedSensors.length > 0 && (
            <div>
              <h5>Query Results ({queriedSensors.length} sensors found):</h5>
              <ul className="list-group">
                {queriedSensors.map(sensor => (
                  <li key={sensor.id || sensor.sensor_id} className="list-group-item">
                    <strong>ID: {sensor.sensor_id}</strong> - Lat: {sensor.latitude.toFixed(4)}, Lon: {sensor.longitude.toFixed(4)} <br />
                    Water Level: {sensor.water_level != null ? sensor.water_level.toFixed(2) + 'm' : 'N/A'},
                    Rainfall: {sensor.rainfall != null ? sensor.rainfall.toFixed(1) + 'mm' : 'N/A'} <br />
                    <small>Timestamp: {new Date(sensor.timestamp).toLocaleString()}</small>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {/* Here you could add a map to display these queriedSensors */}
        </div>
      </div>
    </div>
  );
}