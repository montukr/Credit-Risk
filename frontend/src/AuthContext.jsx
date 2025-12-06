import React, { createContext, useContext, useState } from "react";
import api from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem("token");
    const username = localStorage.getItem("username");
    const role = localStorage.getItem("role");
    return token && username && role ? { token, username, role } : null;
  });

  const login = async (username, password) => {
    const res = await api.post("/auth/login", { username, password });
    const { access_token, role } = res.data;
    const u = { username, role, token: access_token };
    setUser(u);
    localStorage.setItem("token", access_token);
    localStorage.setItem("username", username);
    localStorage.setItem("role", role);
  };

  const register = async ({ username, email, password }) => {
    const res = await api.post("/auth/register", { username, email, password });
    const { access_token, role, username: apiUsername } = res.data;
    const u = { username: apiUsername, role, token: access_token };
    setUser(u);
    localStorage.setItem("token", access_token);
    localStorage.setItem("username", apiUsername);
    localStorage.setItem("role", role);
  };

  const logout = () => {
    setUser(null);
    localStorage.clear();
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
