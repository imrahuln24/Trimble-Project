import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode"; // Ensure you have jwt-decode installed
import { getToken, logout } from "../services/authService";

export default function ProtectedRoute({ children, allowedRoles }) {
  const token = getToken();

  if (!token) {
    // No token, redirect to login (or an unauthorized page if preferred for non-login scenarios)
    return <Navigate to="/" replace />;
  }

  try {
    const decodedToken = jwtDecode(token); // { sub: "username", role: "user_role", exp: 123... }

    // Check for token expiration
    if (decodedToken.exp * 1000 < Date.now()) {
      logout(); // Clear expired token
      return <Navigate to="/" replace />;
    }
    
    if (!allowedRoles || allowedRoles.length === 0) { // If no specific roles required, just needs to be logged in
      return children;
    }

    if (!decodedToken.role || !allowedRoles.includes(decodedToken.role)) {
      return <Navigate to="/unauthorized" replace />; // User role not allowed
    }
    
    return children; // Token valid, role allowed

  } catch (error) {
    console.error("Error decoding token or token invalid:", error);
    logout(); // Clear potentially malformed token
    return <Navigate to="/" replace />;
  }
}

/*import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import { getToken } from "../services/authService";

export default function ProtectedRoute({ children, allowedRoles }) {
  const token = getToken();

  if (!token) return <Navigate to="/unauthorized" />;

  try {
    const decodedToken = jwtDecode(token);
    if (!allowedRoles.includes(decodedToken.role)) {
      return <Navigate to="/unauthorized" />;
    }
    return children;
  } catch {
    return <Navigate to="/unauthorized" />;
  }
}
*/