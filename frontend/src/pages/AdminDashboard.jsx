// src/pages/AdminDashboard.jsx
import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api";

export default function AdminDashboard() {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);
  const [saving, setSaving] = useState(false);

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

  const handleBackToList = () => {
    setSelected(null);
  };

  const handleSaveDetail = async (updated) => {
    if (!selected) return;
    setSaving(true);
    try {
      await api.patch(`/admin/customers/${selected.id}/features`, updated);
      await loadCustomers();
      setSelected((prev) => ({ ...prev, ...updated }));
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  // NEW: fetch full detail (with latest risk_band / last_score) when viewing
  const handleViewCustomer = async (c) => {
    try {
      const res = await api.get(`/admin/customer/${c.id}`);
      setSelected(res.data || c);
    } catch (e) {
      console.error(e);
      // fallback to summary if detail call fails
      setSelected(c);
    }
  };

  return (
    <Layout>
      {!selected ? (
        <>
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
                      <td>{c.username || "-"}</td>
                      <td>{c.CustomerID}</td>
                      <td>₹ {c.CreditLimit}</td>
                      <td>{(c.UtilisationPct || 0).toFixed(1)}%</td>
                      <td>{c.risk_band || "-"}</td>
                      <td>
                        <button
                          type="button"
                          className="pill-btn"
                          onClick={() => handleViewCustomer(c)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={6} className="muted">
                        No customers match this search.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <CustomerDetailPage
          customer={selected}
          onBack={handleBackToList}
          onSave={handleSaveDetail}
          saving={saving}
        />
      )}
    </Layout>
  );
}

function CustomerDetailPage({ customer, onBack, onSave, saving }) {
  const [form, setForm] = useState({
    CreditLimit: customer.CreditLimit || 0,
    UtilisationPct: customer.UtilisationPct || 0,
    AvgPaymentRatio: customer.AvgPaymentRatio || 0,
    MinDuePaidFrequency: customer.MinDuePaidFrequency || 0,
    MerchantMixIndex: customer.MerchantMixIndex || 0,
    CashWithdrawalPct: customer.CashWithdrawalPct || 0,
    RecentSpendChangePct: customer.RecentSpendChangePct || 0,
    DPDBucketNextMonthBinary: customer.DPDBucketNextMonthBinary || 0,
  });

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: Number(value),
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <>
      <button
        type="button"
        className="pill-btn"
        style={{ marginBottom: 12 }}
        onClick={onBack}
      >
        ← Back to portfolio
      </button>

      <h1>{customer.username || customer.CustomerID}</h1>
      <p className="page-caption">
        Full customer profile and ML feature controls for this cardholder.
      </p>

      <form onSubmit={handleSubmit} className="card">
        <div className="card-header">Profile & features</div>

        <div className="row">
          <div className="col">
            <label>
              <span>CustomerID</span>
              <input type="text" value={customer.CustomerID} disabled />
            </label>
            <label>
              <span>Credit limit (₹)</span>
              <input
                type="number"
                name="CreditLimit"
                value={form.CreditLimit}
                onChange={onChange}
              />
            </label>
            <label>
              <span>Utilisation %</span>
              <input
                type="number"
                name="UtilisationPct"
                value={form.UtilisationPct}
                onChange={onChange}
              />
            </label>
            <label>
              <span>Avg payment ratio %</span>
              <input
                type="number"
                name="AvgPaymentRatio"
                value={form.AvgPaymentRatio}
                onChange={onChange}
              />
            </label>
          </div>

          <div className="col">
            <label>
              <span>Min due paid frequency %</span>
              <input
                type="number"
                name="MinDuePaidFrequency"
                value={form.MinDuePaidFrequency}
                onChange={onChange}
              />
            </label>
            <label>
              <span>Merchant mix index</span>
              <input
                type="number"
                step="0.01"
                name="MerchantMixIndex"
                value={form.MerchantMixIndex}
                onChange={onChange}
              />
            </label>
            <label>
              <span>Cash withdrawal %</span>
              <input
                type="number"
                name="CashWithdrawalPct"
                value={form.CashWithdrawalPct}
                onChange={onChange}
              />
            </label>
            <label>
              <span>Recent spend change %</span>
              <input
                type="number"
                name="RecentSpendChangePct"
                value={form.RecentSpendChangePct}
                onChange={onChange}
              />
            </label>
          </div>

          <div className="col">
            <label>
              <span>Next‑month DPD bucket (binary)</span>
              <input
                type="number"
                name="DPDBucketNextMonthBinary"
                value={form.DPDBucketNextMonthBinary}
                onChange={onChange}
              />
            </label>
            <div className="dataset-row" style={{ marginTop: 16 }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                  Current risk band
                </div>
                <div style={{ fontSize: "1.1rem" }}>
                  {customer.risk_band || "-"}
                </div>
                <div className="muted" style={{ fontSize: "0.8rem" }}>
                  Based on latest ML ensemble probability.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save changes"}
          </button>
        </div>
      </form>
    </>
  );
}
