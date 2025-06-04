import axios from "axios";
import { getToken } from "./authService";

const API_URL = "http://127.0.0.1:8000/alerts";

const getAuthHeaders = () => ({
  Authorization: `Bearer ${getToken()}`,
});

// Fetches only the latest 2 unresolved alerts for the top notification
export const fetchLatestUnresolvedAlerts = async () => {
  return axios.get(`${API_URL}/latest-unresolved`, { headers: getAuthHeaders() });
};

// Fetches all alerts (paginated) - can be used for a full alert history page
export const fetchAllAlerts = async (skip = 0, limit = 20) => {
  return axios.get(`${API_URL}/?skip=${skip}&limit=${limit}`, { headers: getAuthHeaders() });
};

export const createAlert = async (alertData) => {
  return axios.post(API_URL + "/", alertData, { headers: getAuthHeaders() });
};

export const resolveAlert = async (alertId) => {
  return axios.put(`${API_URL}/${alertId}/resolve`, {}, { headers: getAuthHeaders() });
};

/*
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

export const fetchAlerts = () => axios.get(`${API_URL}/alerts/`);

export const createAlert = (alert) => axios.post(`${API_URL}/alerts/`, alert);

export const resolveAlert = (id) => axios.put(`${API_URL}/alerts/${id}/resolve`);*/
