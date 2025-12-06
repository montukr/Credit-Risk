import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const nav = useNavigate();

  const handleLogout = () => {
    logout();
    nav("/login");
  };

  return (
    <header className="navbar">
      <div className="navbar-title">
        <span className="logo-mark" />
        <span>NovaCard Risk</span>
      </div>

      <nav className="navbar-links">
        <NavLink
          to="/"
          className={({ isActive }) => (isActive ? "active-link" : "")}
        >
          Overview
        </NavLink>
        {user?.role === "user" && (
          <NavLink
            to="/user/dashboard"
            className={({ isActive }) => (isActive ? "active-link" : "")}
          >
            My Card
          </NavLink>
        )}
        {user?.role === "admin" && (
          <NavLink
            to="/admin/dashboard"
            className={({ isActive }) => (isActive ? "active-link" : "")}
          >
            Portfolio
          </NavLink>
        )}
      </nav>

      <div className="navbar-right">
        {user && (
          <div className="user-pill">
            <span className="icon" />
            <span>{user.username}</span>
            <span className="muted">· {user.role}</span>
          </div>
        )}
        {user ? (
          <button onClick={handleLogout}>Logout</button>
        ) : (
          <button onClick={() => nav("/login")}>Login</button>
        )}
      </div>
    </header>
  );
}
