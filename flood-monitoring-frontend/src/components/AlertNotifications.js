import React, { useEffect, useState, useCallback } from "react";
import { fetchLatestUnresolvedAlerts } from "../services/alertService";

export default function AlertNotifications({ newAlertFromWebSocket }) {
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState('');

  const loadAlerts = useCallback(() => {
    fetchLatestUnresolvedAlerts()
      .then((res) => {
        setAlerts(res.data);
        setError('');
      })
      .catch(err => {
        console.error("Failed to fetch alerts:", err);
        if (err.response && err.response.status === 401) {
            setError("Unauthorized to fetch alerts. Please re-login.");
        } else {
            setError("Could not load alerts.");
        }
      });
  }, []);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  useEffect(() => {
    if (newAlertFromWebSocket) {
      // newAlertFromWebSocket can be { type: 'new_alert', data: {...} } or { type: 'resolved', data: {...} }
      const alertPayload = newAlertFromWebSocket.data; // The actual alert object

      if (newAlertFromWebSocket.type === 'resolved') {
        setAlerts(prevAlerts => prevAlerts.filter(a => a.id !== alertPayload.id));
      } else { // 'new_alert'
        setAlerts(prevAlerts => {
          const isExisting = prevAlerts.find(a => a.id === alertPayload.id);
          if (isExisting) { // If somehow already present, update it (or ignore)
            return prevAlerts.map(a => a.id === alertPayload.id ? alertPayload : a);
          }
          const updatedAlerts = [alertPayload, ...prevAlerts];
          return updatedAlerts.slice(0, 2); // Keep only top 2-3
        });
      }
    }
  }, [newAlertFromWebSocket]);

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  if (!alerts.length) {
    return <div className="alert alert-info">No active critical alerts.</div>;
  }

  return (
    <div className="alert-notifications-container mb-3">
      <h5 className="text-danger">Recent Critical Alerts:</h5>
      <ul className="list-group">
        {alerts.map((alert) => (
          <li key={alert.id} className={`list-group-item list-group-item-${alert.level && alert.level.toLowerCase() === 'high' ? 'danger' : (alert.level && alert.level.toLowerCase() === 'critical' ? 'danger' : 'warning')}`}>
            <strong>{alert.title}</strong>
            <p className="mb-1">{alert.description}</p>
            <small>
              Sensor: {alert.sensor_id || 'N/A'} - Received: {new Date(alert.timestamp).toLocaleString()}
            </small>
          </li>
        ))}
      </ul>
    </div>
  );
}
/*
import React, { useEffect, useState } from "react";
import { fetchAlerts, resolveAlert } from "../services/alertService";

export default function AlertList() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetchAlerts().then((res) => setAlerts(res.data));
  }, []);

  const handleResolve = (id) => {
    resolveAlert(id).then(() => {
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_resolved: true } : a)));
    });
  };

  return (
    <div>
      <h2>Alerts</h2>
      <ul>
        {alerts.map((alert) => (
          <li key={alert.id} style={{ color: alert.is_resolved ? "gray" : "red" }}>
            <strong>{alert.title}</strong> [{alert.level}] - {alert.description}
            <br />
            <small>{new Date(alert.timestamp).toLocaleString()}</small>
            {!alert.is_resolved && (
              <button onClick={() => handleResolve(alert.id)}>Resolve</button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
*/