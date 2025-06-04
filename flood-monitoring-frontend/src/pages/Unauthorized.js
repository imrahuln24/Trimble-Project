import React from 'react';
import { Link } from 'react-router-dom';

export default function Unauthorized() {
  return (
    <div className="container mt-5 text-center">
      <div className="alert alert-warning" role="alert">
        <h1 className="alert-heading">403 - Unauthorized</h1>
        <p>You do not have permission to view this page.</p>
        <hr />
        <p className="mb-0">
          Please contact your administrator if you believe this is an error, or 
          <Link to="/" className="alert-link"> login</Link> with appropriate credentials.
        </p>
        <p className="mt-3">
            <Link to="/dashboard" className="btn btn-primary">Go to Dashboard</Link>
        </p>
      </div>
    </div>
  );
}
/*
import React from "react";

export default function Unauthorized() {
  return (
    <div>
      <h1>403 - Unauthorized</h1>
      <p>You do not have access to this page.</p>
    </div>
  );
}
*/