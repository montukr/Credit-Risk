// App.jsx
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import ProtectedRoute from "./ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import UserDashboard from "./pages/UserDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import AdminOverviewPage from "./pages/AdminOverviewPage";
import AdminModelsPage from "./pages/AdminModelsPage";
import AdminRiskLabPage from "./pages/AdminRiskLabPage";
import Navbar from "./components/Navbar";

function Home() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "admin") {
    // send admins to the Overview page by default
    return <Navigate to="/admin/overview" replace />;
  }
  return <Navigate to="/user/dashboard" replace />;
}

function AppRoutes() {
  return (
    <>
      <Navbar />

      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Role-aware home */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />

        {/* User dashboard */}
        <Route
          path="/user/dashboard"
          element={
            <ProtectedRoute role="user">
              <UserDashboard />
            </ProtectedRoute>
          }
        />

        {/* Admin overview (visual KPIs) */}
        <Route
          path="/admin/overview"
          element={
            <ProtectedRoute role="admin">
              <AdminOverviewPage />
            </ProtectedRoute>
          }
        />

        {/* Admin portfolio (table + per-user view) */}
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute role="admin">
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* Admin: model management */}
        <Route
          path="/admin/models"
          element={
            <ProtectedRoute role="admin">
              <AdminModelsPage />
            </ProtectedRoute>
          }
        />

        {/* Admin: risk lab */}
        <Route
          path="/admin/risk-lab"
          element={
            <ProtectedRoute role="admin">
              <AdminRiskLabPage />
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
