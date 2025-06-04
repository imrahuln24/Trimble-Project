// frontend/src/index.js
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import 'bootstrap/dist/css/bootstrap.min.css';
import 'leaflet/dist/leaflet.css';

import "./index.css";
import "./App.css";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Unauthorized from "./pages/Unauthorized";
import ProtectedRoute from "./components/ProtectedRoute";
import Register from "./pages/Register";
import RiskMap from "./pages/RiskMap";
import SpatialAnalysisPage from "./pages/SpatialAnalysisPage"; // Import the new page

const root = ReactDOM.createRoot(document.getElementById("root"));

const ROLES = {
  ADMIN: "admin",
  FIELD_RESPONDER: "field_responder",
  COMMANDER: "commander",
  GOVERNMENT_OFFICIAL: "government_official",
  VIEWER: "viewer",
};

const ALL_AUTHENTICATED_ROLES = Object.values(ROLES);
// const COMMAND_AND_ABOVE = [ROLES.ADMIN, ROLES.COMMANDER, ROLES.GOVERNMENT_OFFICIAL, ROLES.FIELD_RESPONDER]; // Unused, remove or use
const MAP_VIEWERS = Object.values(ROLES); // All authenticated users can view maps

root.render(
  // <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/unauthorized" element={<Unauthorized />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute allowedRoles={ALL_AUTHENTICATED_ROLES}>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/riskmap"
          element={
            <ProtectedRoute allowedRoles={MAP_VIEWERS}>
              <RiskMap />
            </ProtectedRoute>
          }
        />
        <Route
          path="/spatial-analysis"
          element={
            <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.COMMANDER]}>
              <SpatialAnalysisPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  // </React.StrictMode>
);

/*import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// Import Bootstrap CSS first
import 'bootstrap/dist/css/bootstrap.min.css';
// Import Leaflet CSS (as you already have it)
import 'leaflet/dist/leaflet.css';

// Import your global custom styles AFTER Bootstrap
import "./index.css"; // Your existing global styles (if any specific ones are here)
import "./App.css";   // Import App.css for additional global/component styles

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Unauthorized from "./pages/Unauthorized";
import ProtectedRoute from "./components/ProtectedRoute";
import Register from "./pages/Register";
import RiskMap from "./pages/RiskMap";

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <Router>
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/unauthorized" element={<Unauthorized />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute allowedRoles={['field', 'admin', 'responder', 'official', 'viewer']}>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/riskmap"
        element={
       // <ProtectedRoute allowedRoles={['admin', 'responder', 'field', 'official']}> 
         // <RiskMap />
      //  </ProtectedRoute>
     //   }
    //  />
  //  </Routes>
 // </Router>
//);

/*
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Unauthorized from "./pages/Unauthorized";
import ProtectedRoute from "./components/ProtectedRoute";
import Register from "./pages/Register";
import 'leaflet/dist/leaflet.css';
import RiskMap from "./pages/RiskMap"; 

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <Router>
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/unauthorized" element={<Unauthorized />} />


      <Route
        path="/dashboard"
        element={
          <ProtectedRoute allowedRoles={['field', 'admin', 'responder', 'official', 'viewer']}>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/riskmap"
        element={
        <ProtectedRoute allowedRoles={['admin', 'responder']}>
          <RiskMap />
        </ProtectedRoute>
        }
      />
    </Routes>
  </Router>
);





import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();*/
