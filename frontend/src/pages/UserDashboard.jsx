import React, { useEffect, useState } from "react";
import api from "../api";

export default function UserDashboard() {
  const [summary, setSummary] = useState(null);
  const [txForm, setTxForm] = useState({
    amount: "",
    category: "food",
    description: "",
  });
  const [loadingTx, setLoadingTx] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const [riskRes, txRes] = await Promise.all([
      api.get("/user/risk_summary"),
      api.get("/user/transactions"),
    ]);
    setSummary({
      risk: riskRes.data,
      customer: txRes.data.customer,
      transactions: txRes.data.transactions || [],
    });
    setLoading(false);
  }

  useEffect(() => {
    load().catch(() => setLoading(false));
  }, []);

  const onTxChange = (e) => {
    setTxForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const addTransaction = async (e) => {
    e.preventDefault();
    setLoadingTx(true);
    try {
      await api.post("/user/transactions/add", {
        amount: parseFloat(txForm.amount),
        category: txForm.category,
        description: txForm.description || null,
      });
      setTxForm({ amount: "", category: "food", description: "" });
      await load();
    } finally {
      setLoadingTx(false);
    }
  };

  const utilisation = summary?.customer?.UtilisationPct || 0;
  const creditLimit = summary?.customer?.CreditLimit || 0;

  return (
    <div className="app-root">
      <div className="app-main">

        <h1>My NovaCard</h1>
        <p className="page-caption">
          See your card limit, spending behaviour, and live delinquency risk band.
        </p>

        {loading && <p className="muted">Loading account...</p>}

        {!loading && summary && (
          <>
            <div className="row">
              <div className="col">
                <div className="card">
                  <div className="card-header">Credit line</div>
                  <p style={{ fontSize: "1.4rem", margin: "6px 0" }}>
                    ₹ {creditLimit.toLocaleString()}
                  </p>
                  <p className="muted">
                    Utilisation: {utilisation.toFixed(1)}% of limit
                  </p>
                </div>
              </div>

              <div className="col">
                <div className="card">
                  <div className="card-header">Risk insight</div>
                  <p className="muted" style={{ marginBottom: 6 }}>
                    ML delinquency probability
                  </p>
                  <p style={{ fontSize: "1.1rem", margin: 0 }}>
                    {(summary.risk.ensemble_probability * 100).toFixed(1)}%
                  </p>
                  <p
                    style={{
                      marginTop: 6,
                      fontWeight: 600,
                      color:
                        summary.risk.risk_band === "High"
                          ? "#b91c1c"
                          : summary.risk.risk_band === "Medium"
                          ? "#b45309"
                          : "#166534",
                    }}
                  >
                    {summary.risk.risk_band} risk
                  </p>
                  <p className="muted" style={{ marginTop: 4 }}>
                    Driven by utilisation and repayment behaviour.
                  </p>
                </div>
              </div>
            </div>

            <div className="row">
              <div className="col">
                <div className="card">
                  <div className="card-header">Dummy spending simulator</div>
                  <form onSubmit={addTransaction}>
                    <div className="row">
                      <div className="col">
                        <label>
                          <span>Amount</span>
                          <input
                            name="amount"
                            type="number"
                            value={txForm.amount}
                            onChange={onTxChange}
                            placeholder="2500"
                          />
                        </label>
                      </div>

                      <div className="col">
                        <label>
                          <span>Category</span>
                          <select
                            name="category"
                            value={txForm.category}
                            onChange={onTxChange}
                          >
                            <option value="food">Food & groceries</option>
                            <option value="utilities">Utilities & bills</option>
                            <option value="travel">Travel</option>
                            <option value="entertainment">Entertainment</option>
                            <option value="fuel">Fuel</option>
                            <option value="others">Others</option>
                          </select>
                        </label>
                      </div>
                    </div>

                    <label>
                      <span>Description (optional)</span>
                      <textarea
                        name="description"
                        rows="2"
                        value={txForm.description}
                        onChange={onTxChange}
                        placeholder="Weekend dinner, flight booking..."
                      />
                    </label>

                    <button type="submit" disabled={loadingTx}>
                      {loadingTx ? "Adding..." : "Add dummy transaction"}
                    </button>
                  </form>

                  <p className="muted" style={{ marginTop: 6 }}>
                    Each transaction updates your behavioural features and triggers a
                    fresh risk score.
                  </p>
                </div>
              </div>

              <div className="col">
                <div className="card">
                  <div className="card-header">Recent activity</div>
                  {summary.transactions.length === 0 && (
                    <p className="muted">No dummy transactions yet.</p>
                  )}

                  {summary.transactions.slice(0, 6).map((t) => (
                    <div key={t.id || t._id || t.timestamp} className="dataset-row">
                      <div>
                        <div style={{ fontWeight: 500 }}>₹ {t.amount}</div>
                        <div className="muted">{t.description || t.category}</div>
                      </div>
                      <div className="pill">{t.category}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

          </>
        )}
      </div>
    </div>
  );
}
