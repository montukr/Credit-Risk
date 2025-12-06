import React, { useEffect, useState } from "react";
import api from "../api";

export default function AdminDashboard() {
  const [customers, setCustomers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [newLimit, setNewLimit] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    const res = await api.get("/admin/customers");
    setCustomers(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load().catch(() => setLoading(false));
  }, []);

  const onRowClick = (c) => {
    setSelected(c);
    setNewLimit(String(c.CreditLimit));
  };

  const saveLimit = async () => {
    if (!selected) return;
    const val = parseFloat(newLimit);
    if (!val) return;
    setSaving(true);
    try {
      await api.patch(`/admin/customers/${selected.id}/credit_limit`, {
        credit_limit: val,
      });
      await load();
      const updated = customers.find((x) => x.id === selected.id);
      setSelected(updated || null);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="app-root">
      <div className="app-main">

        <h1>Portfolio overview</h1>
        <p className="page-caption">
          Monitor customer utilisation and adjust credit lines based on risk.
        </p>

        <div className="card">
          <div className="card-header">Customer list</div>
          {loading && <p className="muted">Loading customers...</p>}
          {!loading && (
            <div className="preview-table">
              <table>
                <thead>
                  <tr>
                    <th>CustomerID</th>
                    <th>Credit limit</th>
                    <th>Utilisation %</th>
                    <th>Risk band</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.map((c) => (
                    <tr
                      key={c.id}
                      style={{
                        cursor: "pointer",
                        background:
                          selected?.id === c.id
                            ? "rgba(191,219,254,0.4)"
                            : "white",
                      }}
                      onClick={() => onRowClick(c)}
                    >
                      <td>{c.CustomerID}</td>
                      <td>₹ {c.CreditLimit.toLocaleString()}</td>
                      <td>{c.UtilisationPct.toFixed(1)}%</td>
                      <td>{c.risk_band || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {selected && (
          <div className="card">
            <div className="card-header">
              Manage credit line · {selected.CustomerID}
            </div>
            <div className="row">
              <div className="col">
                <p className="muted">
                  Current limit: ₹ {selected.CreditLimit.toLocaleString()}
                </p>
                <label>
                  <span>New credit limit</span>
                  <input
                    type="number"
                    value={newLimit}
                    onChange={(e) => setNewLimit(e.target.value)}
                  />
                </label>
                <button onClick={saveLimit} disabled={saving}>
                  {saving ? "Saving..." : "Save change"}
                </button>
              </div>
              <div className="col">
                <p className="muted">
                  Utilisation: {selected.UtilisationPct.toFixed(1)}%
                </p>
                <p className="muted">
                  Risk band: {selected.risk_band || "not scored yet"}
                </p>
                <p className="info-text">
                  For demo, risk bands come from the ML delinquency model.
                </p>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
