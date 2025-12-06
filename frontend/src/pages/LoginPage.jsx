import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
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
      await login(form.username, form.password);
      nav("/");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (Array.isArray(detail)) {
        // validation error array from FastAPI
        setError(detail[0]?.msg || "Invalid input");
      } else if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-root">
      <div className="auth-card">
        <h1>Sign in to NovaCard</h1>
        <p className="page-caption">
          Access your credit card, spending insights, and risk profile.
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
                placeholder="admin"
              />
            </label>
          </div>
          <div>
            <label>
              <span>Password</span>
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
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
        <p className="muted" style={{ marginTop: 10 }}>
          New customer?{" "}
          <Link to="/register">Create an account</Link>
        </p>
      </div>
    </div>
  );
}
