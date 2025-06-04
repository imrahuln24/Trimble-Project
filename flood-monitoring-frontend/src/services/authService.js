// frontend/src/services/authService.js
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

export const login = async (username, password) => {
  const response = await axios.post(
    `${API_URL}/login`,
    new URLSearchParams({ username, password }),
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );
  if (response.data.access_token) {
    sessionStorage.setItem("token", response.data.access_token); // Use sessionStorage
  }
  return response.data;
};

export const register = async (username, password, role) => {
  return axios.post(`${API_URL}/register`, { username, password, role });
};

export const logout = () => {
  sessionStorage.removeItem("token"); // Use sessionStorage
};

export const getToken = () => {
  return sessionStorage.getItem("token"); // Use sessionStorage
};

// getCurrentUser can remain as is conceptually, or be removed if fetchUserDetails is always used.
export const getCurrentUser = () => {
  const token = getToken();
  if (token) {
    return { token };
  }
  return null;
};

export const fetchUserDetails = async () => {
  const token = getToken();
  if (!token) return null;
  try {
    const response = await axios.get(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    console.error("Failed to fetch user details:", error);
    if (error.response && error.response.status === 401) {
        logout(); // Auto-logout on 401
    }
    return null;
  }
};
/*
import axios from "axios";

const API_URL = "http://127.0.0.1:8000"; // Ensure this is correct

export const login = async (username, password) => {
  const response = await axios.post(
    `${API_URL}/login`,
    new URLSearchParams({ username, password }), // FastAPI OAuth2PasswordRequestForm expects form data
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );
  if (response.data.access_token) {
    localStorage.setItem("token", response.data.access_token);
  }
  return response.data;
};

export const register = async (username, password, role) => {
  return axios.post(`${API_URL}/register`, { username, password, role });
};

export const logout = () => {
  localStorage.removeItem("token");
};

export const getToken = () => {
  return localStorage.getItem("token");
};

export const getCurrentUser = () => {
  const token = getToken();
  if (token) {
    // You would typically decode the token here to get user info
    // For simplicity, we'll assume you fetch user details separately or decode on demand
    // For now, this just indicates a token exists
    return { token }; 
  }
  return null;
};

// Add this if you need to fetch user details after login for role display, etc.
export const fetchUserDetails = async () => {
  const token = getToken();
  if (!token) return null;
  try {
    const response = await axios.get(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data; // { id, username, role }
  } catch (error) {
    console.error("Failed to fetch user details:", error);
    // Could logout user if token is invalid (e.g., 401 error)
    // if (error.response && error.response.status === 401) logout();
    return null;
  }
};


import axios from 'axios';

const API_URL = "http://localhost:8000";

export const login = async (username, password) => {
  const response = await axios.post(`${API_URL}/login`, new URLSearchParams({
    username,
    password
  }));
  sessionStorage.setItem("token", response.data.access_token);
};

export const logout = () => {
  sessionStorage.removeItem("token");
};

export const getToken = () => sessionStorage.getItem("token");
*/