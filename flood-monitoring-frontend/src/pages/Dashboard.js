// frontend/src/pages/Dashboard.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
// import { jwtDecode } from "jwt-decode"; // Removed as it's unused
import { getToken, fetchUserDetails, logout } from "../services/authService";
import LiveMap from "../LiveMap";
import AlertNotifications from "../components/AlertNotifications";
import Chat from "../components/Chat";
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

export default function Dashboard() {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newAlertMessage, setNewAlertMessage] = useState(null); // Renamed for clarity
  const [sensorUpdateFromWebSocket, setSensorUpdateFromWebSocket] = useState(null);
  const generalWs = useRef(null);
  const navigate = useNavigate();

  const setupGeneralWebSocket = useCallback(() => {
    if (generalWs.current && (generalWs.current.readyState === WebSocket.OPEN || generalWs.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    generalWs.current = new WebSocket('ws://127.0.0.1:8000/ws/general');

    generalWs.current.onopen = () => console.log("General WebSocket Connected");

    generalWs.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "new_alert") {
          console.log("New alert via WebSocket:", message.data);
          setNewAlertMessage({ type: 'new_alert', data: message.data }); // Pass full message structure
        } else if (message.type === "sensor_update") {
          // console.log("Sensor update via WebSocket:", message.data);
          setSensorUpdateFromWebSocket(message.data);
        } else if (message.type === "alert_resolved") {
          console.log("Alert resolved via WebSocket:", message.data);
          setNewAlertMessage({ type: 'resolved', data: message.data }); // Pass full message structure
        }
      } catch (e) {
        console.error("Error processing WebSocket message:", e, "Data:", event.data);
      }
    };
    generalWs.current.onclose = (event) => {
        console.log("General WebSocket Disconnected. Attempting reconnect...", event.reason);
        // Implement a robust reconnect strategy (e.g., exponential backoff)
        // Avoid reconnecting if logout is in progress or user is not authenticated
        if (getToken()) { // Only reconnect if a token still exists
             setTimeout(setupGeneralWebSocket, 5000); // Simple reconnect attempt
        }
    };
    generalWs.current.onerror = (err) => console.error("General WebSocket Error:", err);

  }, []); // Removed navigate from dependencies as it's stable


  useEffect(() => {
    const token = getToken();
    if (!token) {
      setError("No token found. Please login.");
      setLoading(false);
      if (window.location.pathname !== "/") navigate("/"); // Avoid recursive navigation if already on login
      return;
    }

    let isMounted = true; // Prevent state updates on unmounted component

    fetchUserDetails()
      .then(userData => {
        if (!isMounted) return;
        if (userData) {
          setCurrentUser(userData);
          setupGeneralWebSocket();
        } else {
          setError("Failed to fetch user details. Session might be invalid.");
          logout();
          if (window.location.pathname !== "/") navigate("/");
        }
      })
      .catch(() => {
        if (!isMounted) return;
        setError("Error fetching user details. Please try logging in again.");
        logout();
        if (window.location.pathname !== "/") navigate("/");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
      if (generalWs.current) {
        console.log("Closing general WebSocket connection on Dashboard unmount.");
        generalWs.current.close();
      }
    };
  }, [navigate, setupGeneralWebSocket]); // setupGeneralWebSocket is memoized

  if (loading) {
    return <div className="container mt-5 text-center"><p>Loading dashboard...</p></div>;
  }

  if (error || !currentUser) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger text-center" role="alert">
          <h4>Access Error</h4>
          <p>{error || "Could not load user data."} Please <a href="/" onClick={(e) => { e.preventDefault(); navigate('/'); }} className="alert-link">login</a>.</p>
        </div>
      </div>
    );
  }

  const { role, username } = currentUser;

  const canViewRiskMapButton = [
    "admin", "field_responder", "commander", "government_official", "viewer" // Viewers can also see RiskMap
  ].includes(role);

  const canViewFullLiveMap = [
    "admin", "field_responder", "commander"
  ].includes(role);


  return (
    <div className="container-fluid dashboard-container py-3 px-md-4">
      <header className="dashboard-header mb-3 d-flex justify-content-between align-items-center">
        <h1 className="display-6 mb-0">Welcome, {username} ({role.replace('_', ' ').toUpperCase()})</h1>
        <button className="btn btn-outline-secondary btn-sm" onClick={() => { logout(); navigate('/'); }}>Logout</button>
      </header>

      <AlertNotifications newAlertFromWebSocket={newAlertMessage} />

      <div className="row">
        <div className="col-lg-8 col-md-7 mb-3">
          <section className="dashboard-section card shadow-sm">
            <div className="card-body">
              <h3 className="card-title h5">
                {/* Role-specific titles */}
                {role === "viewer" && "Live Situation Overview"}
                {role === "field_responder" && "Field Sensor Live Map"}
                {role === "commander" && "Command Center Live Map"}
                {role === "admin" && "System Live Map Overview"}
                {role === "government_official" && "Regional Live Situation"}
              </h3>

              {canViewRiskMapButton && (
                <button
                  onClick={() => navigate("/riskmap")}
                  className="btn btn-info btn-sm mb-3 me-2"
                >
                  View Detailed Risk Map
                </button>
              )}
               {["admin", "commander"].includes(role) && (
                <button onClick={() => navigate("/spatial-analysis")} className="btn btn-outline-secondary btn-sm mb-3">
                    Spatial Analysis Tools
                </button>
               )}

              {canViewFullLiveMap || role === "viewer" || role === "government_official" ? (
                <div className="live-map-wrapper" style={{ height: '60vh', minHeight: '400px' }}>
                  <LiveMap sensorUpdateFromWebSocket={sensorUpdateFromWebSocket} />
                </div>
              ) : (
                <p className="text-muted">Map view restricted for this role.</p>
              )}
               <p className="card-text text-muted small mt-2">
                {/* Role-specific descriptions */}
                {role === "field_responder" && "Real-time data from field sensors."}
                {role === "commander" && "Centralized monitoring and response coordination."}
                {role === "government_official" && "Aggregated risk data and insights."}
                {role === "viewer" && "General overview of active sensors."}
              </p>
            </div>
          </section>
        </div>

        <div className="col-lg-4 col-md-5 mb-3">
          {["admin", "field_responder", "commander", "government_official"].includes(role) && (
            <Chat currentUser={currentUser} />
          )}
        </div>
      </div>
    </div>
  );
}



/*

import { jwtDecode } from "jwt-decode";
import { getToken } from "../services/authService";
import LiveMap from "../LiveMap";
import AlertList from "../components/AlertNotifications";
import { useNavigate } from 'react-router-dom';

console.log("Dashboard loaded");

export default function Dashboard() {
  const token = getToken();
  const navigate = useNavigate();

  if (!token) {
    console.error("No token found");
    return (
      <div className="container mt-5">
        <div className="alert alert-danger text-center" role="alert">
          <h4>Access Denied</h4>
          <p>No token found. Please <a href="/" className="alert-link">login</a> to continue.</p>
        </div>
      </div>
    );
  }

  let role;
  try {
    const decoded = jwtDecode(token);
    role = decoded.role;
    console.log("Decoded role:", role);
  } catch (e) {
    console.error("JWT decode failed", e);
    return (
      <div className="container mt-5">
        <div className="alert alert-danger text-center" role="alert">
          <h4>Invalid Session</h4>
          <p>Your session is invalid or has expired. Please <a href="/" className="alert-link">login</a> again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid dashboard-container py-4 px-md-5">
      <header className="dashboard-header mb-4 pt-3">
        <h1 className="display-5">Welcome, {role.toUpperCase()}</h1>
      </header>

      <section className="alert-list-section card shadow-sm mb-5">
        <div className="card-body">
          <h2 className="card-title h4">Alerts</h2>
          
          <AlertList />
        </div>
      </section>

      {["admin", "field"].includes(role) && (
        <section className="dashboard-section card shadow-sm mb-4">
          <div className="card-body">
            <h3 className="card-title h5">Live Sensor Monitoring (Field)</h3>
            <p className="card-text text-muted">Real-time data from field sensors and risk map access.</p>
            <button
              onClick={() => navigate("/riskmap")}
              className="btn btn-info dashboard-button" // Changed to btn-info for variety
            >
              View Risk Map
            </button>
            <div className="mt-3">
              <LiveMap />
            </div>
          </div>
        </section>
      )}

      {["responder", "official"].includes(role) && (
        <section className="dashboard-section card shadow-sm mb-4">
          <div className="card-body">
            <h3 className="card-title h5">Command Center Overview</h3>
            <p className="card-text text-muted">Centralized monitoring, response coordination, and risk map.</p>
            <button
              onClick={() => navigate("/riskmap")}
              className="btn btn-primary dashboard-button"
            >
              View Risk Map
            </button>
            <div className="mt-3">
              <LiveMap />
            </div>
          </div>
        </section>
      )}

      {role === "viewer" && (
        <section className="dashboard-section card shadow-sm mb-4">
          <div className="card-body">
            <h3 className="card-title h5">Top-Level Risk Analysis Dashboard</h3>
            <p className="card-text text-muted">Aggregated risk data and insights via live map.</p>
            <div className="mt-3">
              <LiveMap />
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

import { jwtDecode } from "jwt-decode";
import { getToken } from "../services/authService";
import LiveMap from "../LiveMap";
import AlertList from "../components/AlertList";
import { useNavigate } from 'react-router-dom';


console.log("Dashboard loaded");


export default function Dashboard() {
  const token = getToken();
  const navigate = useNavigate();
  //const { role } = jwtDecode(token);
  if (!token) {
    console.error("No token found");
    return <div>No token found</div>;
  }

  let role;
  const decoded = jwtDecode(token);
  console.log("token:", token)
  console.log("Decoded token:", decoded)
  try {
    const decoded = jwtDecode(token);
    console.log("token:", token)
    console.log("Decoded token:", decoded)
    role = decoded.role;
    console.log("Decoded role:", role);
  } catch (e) {
    console.error("JWT decode failed", e);
    return <div>Invalid token</div>;
  }
  //field commander official
  return (

    <div>
      <h1>Welcome, {role.toUpperCase()}</h1>
      <AlertList />
      {["admin", "field"].includes(role) && (
        <>
        
          <p>Live Sensor Monitoring (Field)</p>
          <button onClick={() => navigate("/riskmap")}>View Risk Map</button>
          <LiveMap />
        </>
      )}

      {["responder", "official"].includes(role) && (
        <>
          <p>Command Center Overview</p>
          <button onClick={() => navigate("/riskmap")}>View Risk Map</button>
          <LiveMap />
        </>
      )}

      {role === "viewer" && (
        <>
          <p>Top-Level Risk Analysis Dashboard</p>
          <LiveMap />
        </>
      )}
    </div>
  );
}
*/