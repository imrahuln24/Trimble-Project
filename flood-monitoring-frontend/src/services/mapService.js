// frontend/src/services/mapService.js
import axios from "axios";
import { getToken } from "./authService";

const API_URL = "http://127.0.0.1:8000"; // Base API URL

const getAuthHeaders = () => ({
  Authorization: `Bearer ${getToken()}`,
});

// Fetches data for the dynamic risk map (dots on map, heatmap data)
export const fetchRiskMapData = async () => {
  // Corrected URL: The endpoint is now under the /spatial prefix in spatial_router.py
  return axios.get(`${API_URL}/spatial/risk-map-data`, { headers: getAuthHeaders() });
};

// Fetches sensors within a given radius around a lat/lon point
export const fetchSensorsInRadius = async (latitude, longitude, radius_km, min_water_level = null) => {
  let params = { latitude, longitude, radius_km };
  if (min_water_level !== null) {
    params.min_water_level = min_water_level;
  }
  // Corrected URL: The endpoint is under the /spatial prefix
  return axios.get(`${API_URL}/spatial/sensors-in-radius`, {
    headers: getAuthHeaders(),
    params: params,
  });
};

// Note: LiveMap.js fetches initial sensor data from /sensor-data (defined in sensor_router.py without a prefix, or in main.py)
// This is separate from risk map data or spatial queries.