import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api";

export default function AdminOverviewPage() {
  const [stats, setStats] = useState({
    total_customers: 0,
    flagged_customers: 0,
    high_risk: 0,
    medium_risk: 0,
    low_risk: 0,
  });
  const [topUsers, setTopUsers] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get("/admin/customers");
        const customers = res.data || [];

        const total = customers.length;
        const high = customers.filter((c) => c.risk_band === "High").length;
        const med = customers.filter((c) => c.risk_band === "Medium").length;
        const low = customers.filter((c) => c.risk_band === "Low").length;
        const flagged = high + med;

        setStats({
          total_customers: total,
          flagged_customers: flagged,
          high_risk: high,
          medium_risk: med,
          low_risk: low,
        });

        const top = [...customers]
          .sort((a, b) => (b.UtilisationPct || 0) - (a.UtilisationPct || 0))
          .slice(0, 5);
        setTopUsers(top);
      } catch (e) {
        console.error(e);
      }
    };

    fetchData();
  }, []);

  return (
    <Layout>
      <h1>Portfolio overview</h1>
      <p className="page-caption">
        High‑level health of the credit card book: customer counts, risk flags, and top risk accounts.
      </p>

      <div className="cards-row">
        <div className="card kpi-card">
          <div className="card-header">Total customers</div>
          <p className="kpi-number">{stats.total_customers}</p>
        </div>
        <div className="card kpi-card">
          <div className="card-header">Flagged customers</div>
          <p className="kpi-number">{stats.flagged_customers}</p>
          <p className="muted">High + Medium risk</p>
        </div>
        <div className="card kpi-card">
          <div className="card-header">High risk</div>
          <p className="kpi-number">{stats.high_risk}</p>
        </div>
        <div className="card kpi-card">
          <div className="card-header">Medium risk</div>
          <p className="kpi-number">{stats.medium_risk}</p>
        </div>
      </div>

      <div className="card">
        <div className="card-header">Risk distribution</div>
        <div className="risk-bar">
          <div
            className="risk-segment high"
            style={{ flex: stats.high_risk || 0 }}
          >
            High ({stats.high_risk})
          </div>
          <div
            className="risk-segment medium"
            style={{ flex: stats.medium_risk || 0 }}
          >
            Medium ({stats.medium_risk})
          </div>
          <div
            className="risk-segment low"
            style={{ flex: stats.low_risk || 0 }}
          >
            Low ({stats.low_risk})
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">Top accounts by utilisation</div>
        {topUsers.length === 0 ? (
          <p className="muted">No customers yet.</p>
        ) : (
          <div className="preview-table">
            <table>
              <thead>
                <tr>
                  <th>Username</th>
                  <th>CustomerID</th>
                  <th>Utilisation %</th>
                  <th>Credit limit</th>
                  <th>Risk band</th>
                </tr>
              </thead>
              <tbody>
                {topUsers.map((c) => (
                  <tr key={c.id || c._id}>
                    <td>{c.username || c.CustomerID}</td>
                    <td>{c.CustomerID}</td>
                    <td>{(c.UtilisationPct || 0).toFixed(1)}%</td>
                    <td>₹ {c.CreditLimit}</td>
                    <td>{c.risk_band || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
