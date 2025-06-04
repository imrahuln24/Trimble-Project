import axios from "axios";
import { getToken } from "./authService";

const API_URL = "http://127.0.0.1:8000/chat";

const getAuthHeaders = () => ({
  Authorization: `Bearer ${getToken()}`,
});

export const fetchChatMessages = async (skip = 0, limit = 50) => {
  return axios.get(`${API_URL}/messages?skip=${skip}&limit=${limit}`, { headers: getAuthHeaders() });
};

// Sending messages will be handled via WebSocket in the component