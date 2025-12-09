import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="navbar">
      {/* Left Branding */}
      <div className="navbar-title">
        <span className="logo-mark" />
        <span>HDFC Credit Card</span>
      </div>

      {/* Center Navigation Links */}
      <nav className="navbar-links">
        {user && (
          <>
            {/* Admin Dashboard */}
            {user.role === "admin" && (
              <NavLink
                to="/admin/overview"
                className={({ isActive }) => (isActive ? "active-link" : "")}
              >
                Dashboard
              </NavLink>
            )}

            {/* User Dashboard Link */}
            {user.role === "user" && (
              <NavLink
                to="/user/dashboard"
                className={({ isActive }) => (isActive ? "active-link" : "")}
                style={{ minWidth: "90px", textAlign: "center" }}  // ← slightly wider
              >
                My Card
              </NavLink>
            )}

            {/* Admin Links */}
            {user.role === "admin" && (
              <>
                <NavLink
                  to="/admin/dashboard"
                  className={({ isActive }) =>
                    isActive ? "active-link" : ""
                  }
                >
                  Portfolio
                </NavLink>

                <NavLink
                  to="/admin/models"
                  className={({ isActive }) =>
                    isActive ? "active-link" : ""
                  }
                >
                  Models
                </NavLink>

                <NavLink
                  to="/admin/risk-lab"
                  className={({ isActive }) =>
                    isActive ? "active-link" : ""
                  }
                >
                  Risk Lab
                </NavLink>
              </>
            )}
          </>
        )}
      </nav>

      {/* Right Side User + Logout */}
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
          <button onClick={() => navigate("/login")}>Login</button>
        )}
      </div>
    </header>
  );
}
