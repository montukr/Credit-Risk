import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api";

function CustomerDetailDrawer({ customer, onClose, onUpdated }) {
  const [limit, setLimit] = useState(customer.CreditLimit);

  const saveLimit = async () => {
    await api.patch(`/admin/customers/${customer.id}/credit_limit`, {
      credit_limit: Number(limit),
    });
    await onUpdated();
  };

  return (
    <div className="drawer">
      <div className="drawer-header">
        <h3>{customer.username || customer.CustomerID}</h3>
        <button type="button" onClick={onClose}>
          ×
        </button>
      </div>
      <div className="drawer-body">
        <p>CustomerID: {customer.CustomerID}</p>
        <p>Current risk band: {customer.risk_band || "-"}</p>
        <p>Utilisation: {(customer.UtilisationPct || 0).toFixed(1)}%</p>

        <label>
          <span>Credit limit (₹)</span>
          <input
            type="number"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
          />
        </label>
        <button type="button" onClick={saveLimit}>
          Save credit limit
        </button>

        {/* Extend here with controls: spend_cap, category_blocks, alerts_enabled */}
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);

  const loadCustomers = async () => {
    const res = await api.get("/admin/customers");
    setCustomers(res.data || []);
  };

  useEffect(() => {
    loadCustomers().catch(console.error);
  }, []);

  const filtered = customers.filter((c) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    const uname = (c.username || "").toLowerCase();
    const cid = (c.CustomerID || "").toLowerCase();
    return uname.includes(q) || cid.includes(q);
  });

  return (
    <Layout>
      <h1>Customer portfolio</h1>
      <p className="page-caption">
        Search and manage individual cardholders: limits, controls, and risk posture.
      </p>

      <div className="card">
        <div
          className="card-header"
          style={{ display: "flex", justifyContent: "space-between" }}
        >
          <span>Customers</span>
          <input
            type="text"
            placeholder="Search by username / CustomerID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 260 }}
          />
        </div>
        <div className="preview-table">
          <table>
            <thead>
              <tr>
                <th>Username</th>
                <th>CustomerID</th>
                <th>Credit limit</th>
                <th>Utilisation %</th>
                <th>Risk band</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id}>
                  <td>{c.username || c.CustomerID}</td>
                  <td>{c.CustomerID}</td>
                  <td>₹ {c.CreditLimit}</td>
                  <td>{(c.UtilisationPct || 0).toFixed(1)}%</td>
                  <td>{c.risk_band || "-"}</td>
                  <td>
                    <button
                      type="button"
                      className="pill-btn"
                      onClick={() => setSelected(c)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selected && (
        <CustomerDetailDrawer
          customer={selected}
          onClose={() => setSelected(null)}
          onUpdated={loadCustomers}
        />
      )}
    </Layout>
  );
}
