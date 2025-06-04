// frontend/src/pages/Register.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register as registerService } from "../services/authService";

export default function Register() {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    role: "viewer",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate(); // Now used

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!formData.username || !formData.password || !formData.role) {
        setError("All fields are required.");
        return;
    }
    try {
      await registerService(formData.username, formData.password, formData.role);
      setSuccess("Registration successful! Redirecting to login...");
      setTimeout(() => {
        navigate("/"); // Redirect to login after a short delay
      }, 2000);
    } catch (err) {
      // ... (error handling remains the same)
      if (err.response && err.response.data && err.response.data.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === "string") {
          setError(detail);
        } else if (Array.isArray(detail)) {
          setError(detail.map((d) => `${d.loc.join(".")} - ${d.msg}`).join("; "));
        } else {
          setError("Registration failed. An unexpected error occurred.");
        }
      } else {
        setError("Registration failed. Please try again.");
      }
      console.error("Registration error:", err);
    }
  };

  // ... (return JSX remains the same)
  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card shadow-sm">
            <div className="card-body p-4">
              <h2 className="card-title text-center mb-4">Register New Account</h2>
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="usernameInput" className="form-label">Username</label>
                  <input
                    type="text"
                    className="form-control"
                    id="usernameInput"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="passwordInput" className="form-label">Password</label>
                  <input
                    type="password"
                    className="form-control"
                    id="passwordInput"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="roleSelect" className="form-label">Role</label>
                  <select
                    className="form-select"
                    id="roleSelect"
                    name="role"
                    value={formData.role}
                    onChange={handleChange}
                  >
                    <option value="viewer">Viewer (Basic Access)</option>
                    <option value="field_responder">Field Responder</option>
                    <option value="commander">Commander</option>
                    <option value="government_official">Government Official</option>
                    <option value="admin">System Administrator</option>
                  </select>
                </div>

                {error && <div className="alert alert-danger p-2">{error}</div>}
                {success && <div className="alert alert-success p-2">{success}</div>}

                <div className="d-grid">
                    <button type="submit" className="btn btn-primary">Register</button>
                </div>
              </form>
              <p className="mt-3 text-center">
                Already have an account? <a href="/">Login here</a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/*
import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    role: "viewer",
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
  e.preventDefault();
  setError("");
  try {
    await axios.post("http://127.0.0.1:8000/register", formData);
    alert("Registration successful! Please login.");
    navigate("/");
  } catch (err) {
    // Try to extract error message string safely
    if (err.response && err.response.data) {
      // If backend sends an object with 'detail' as string or array
      const detail = err.response.data.detail;

      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail)) {
        // Pydantic validation errors often come as array of objects
        const messages = detail.map((d) => d.msg).join(", ");
        setError(messages);
      } else {
        setError("Registration failed");
      }
    } else {
      setError("Registration failed");
    }
  }
};

  return (
    <div style={{ maxWidth: 400, margin: "auto", paddingTop: 40 }}>
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Username
          <input
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
          />
        </label>

        <label>
          Password
          <input
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
        </label>

        <label>
          Role
          <select name="role" value={formData.role} onChange={handleChange}>
            <option value="admin">Field Responder</option>
            <option value="responder">Commander</option>
            <option value="viewer">Government Official</option>
          </select>
        </label>

        {error && <p style={{ color: "red" }}>{error}</p>}

        <button type="submit">Register</button>
      </form>
    </div>
  );
}*/
