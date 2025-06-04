import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/authService";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Login failed. Please check your credentials.");
      }
      console.error("Login error:", err);
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-4">
          <div className="card shadow-sm">
            <div className="card-body p-4">
              <h2 className="card-title text-center mb-4">Flood Monitor Login</h2>
              <form onSubmit={handleLogin}>
                <div className="mb-3">
                  <label htmlFor="usernameInput" className="form-label">Username</label>
                  <input
                    type="text"
                    className="form-control"
                    id="usernameInput"
                    placeholder="Enter username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="passwordInput" className="form-label">Password</label>
                  <input
                    type="password"
                    className="form-control"
                    id="passwordInput"
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                {error && <div className="alert alert-danger p-2">{error}</div>}
                <div className="d-grid">
                  <button type="submit" className="btn btn-primary">Login</button>
                </div>
              </form>
              <p className="mt-3 text-center">
                Don't have an account? <a href="/register">Register here</a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
/*
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/authService";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (err) {
      alert("Login failed");
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input placeholder="Username" onChange={(e) => setUsername(e.target.value)} />
      <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Login</button>
      <p>Don't have an account? <a href="/register">Register here</a></p>
    </form>
    
  );
}

*/