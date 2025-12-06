import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      nav("/");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail[0]?.msg || "Invalid input");
      } else if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Registration failed. Please check your input.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-root">
      <div className="auth-card">
        <h1>Create NovaCard account</h1>
        <p className="page-caption">
          Password can be as short as 4 characters for this sandbox.
        </p>
        {error && <p className="error-text">{error}</p>}
        <form onSubmit={onSubmit}>
          <div>
            <label>
              <span>Username</span>
              <input
                name="username"
                value={form.username}
                onChange={onChange}
                placeholder="jane.doe"
              />
            </label>
          </div>
          <div>
            <label>
              <span>Email</span>
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={onChange}
                placeholder="you@example.com"
              />
            </label>
          </div>
          <div>
            <label>
              <span>Password (min 4 chars)</span>
              <input
                name="password"
                type="password"
                value={form.password}
                onChange={onChange}
                placeholder="••••"
              />
            </label>
          </div>
          <button type="submit" disabled={loading}>
            {loading ? "Creating..." : "Create account"}
          </button>
        </form>
        <p className="muted" style={{ marginTop: 10 }}>
          Already have an account?{" "}
          <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
