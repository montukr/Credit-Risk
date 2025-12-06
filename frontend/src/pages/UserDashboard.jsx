import React, { useEffect, useState } from "react";
import api from "../api";

export default function UserDashboard() {
  const [summary, setSummary] = useState(null);
  const [txForm, setTxForm] = useState({
    amount: "",
    category: "food_online", // Updated initial category
    description: "",
  });
  const [loadingTx, setLoadingTx] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      // Fetch both risk summary and transactions in parallel
      const [riskRes, txRes] = await Promise.all([
        api.get("/user/risk_summary"),
        api.get("/user/transactions"),
      ]);
      setSummary({
        risk: riskRes.data,
        customer: txRes.data.customer,
        transactions: txRes.data.transactions || [],
      });
    } catch (error) {
      console.error("Error loading dashboard data:", error);
      // Handle error, maybe set an error state
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load().catch(() => setLoading(false));
  }, []);

  const onTxChange = (e) => {
    setTxForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const addTransaction = async (e) => {
    e.preventDefault();
    // Simple validation
    if (!txForm.amount || isNaN(parseFloat(txForm.amount)) || parseFloat(txForm.amount) <= 0) {
      alert("Please enter a valid positive amount.");
      return;
    }
    
    setLoadingTx(true);
    try {
      await api.post("/user/transactions/add", {
        amount: parseFloat(txForm.amount),
        category: txForm.category,
        description: txForm.description || null,
      });
      // Reset form and reload data
      setTxForm({ amount: "", category: "food_online", description: "" });
      await load();
    } catch (error) {
      console.error("Error adding transaction:", error);
    } finally {
      setLoadingTx(false);
    }
  };

  const customer = summary?.customer;
  const risk = summary?.risk;
  const txs = summary?.transactions || [];

  return (
    <div className="app-root">
      <div className="app-main">

        <h1>My HDFC Credit Card</h1>
        <p className="page-caption">
          See your card stats, recent spends, and how your behaviour impacts delinquency risk.
        </p>

        {loading && <p className="muted">Loading account...</p>}

        {!loading && summary && (
          <>
            {/* 1. Feature Snapshot / Account Overview */}
            <div className="card">
              <div className="card-header">Account and Behavioural Snapshot</div>
              <div className="row">
                <div className="col">
                  <p>Customer ID: <strong>{customer.CustomerID}</strong></p>
                  <p>Credit limit: <strong>₹ {customer.CreditLimit.toLocaleString()}</strong></p>
                  <p>Utilisation: <strong>{customer.UtilisationPct?.toFixed(1)}%</strong></p>
                  <p style={{ marginTop: '10px' }}>
                    Current Risk Band:
                    <strong
                      style={{
                        marginLeft: '5px',
                        color:
                          risk.risk_band === "High"
                            ? "#b91c1c"
                            : risk.risk_band === "Medium"
                            ? "#b45309"
                            : "#166534",
                      }}
                    >
                      {risk.risk_band} ({ (risk.ensemble_probability * 100).toFixed(1) }%)
                    </strong>
                  </p>
                </div>
                
                {/* Behavioral features - Left column */}
                <div className="col">
                  <p>Avg payment ratio: <strong>{customer.AvgPaymentRatio?.toFixed(1)}%</strong></p>
                  <p>Min due paid freq: <strong>{customer.MinDuePaidFrequency?.toFixed(1)}%</strong></p>
                  <p>Cash withdrawal %: <strong>{customer.CashWithdrawalPct?.toFixed(1)}%</strong></p>
                </div>
                
                {/* Behavioral features - Right column */}
                <div className="col">
                  <p>Merchant mix index: <strong>{customer.MerchantMixIndex?.toFixed(2)}</strong></p>
                  <p>Recent spend change: <strong>{customer.RecentSpendChangePct?.toFixed(1)}%</strong></p>
                  <p>Time since last transaction: <strong>{customer.TimeSinceLastTxDays || '-'} days</strong></p>
                </div>
              </div>
              <p className="info-text" style={{ marginTop: '10px' }}>
                Your **Current Risk Band** is driven by the ML delinquency model, which uses these behavioural features.
              </p>
            </div>

            {/* 2. Spend Simulator */}
            <div className="card">
              <div className="card-header">Simulate a new spend</div>
              <form onSubmit={addTransaction}>
                <div className="row">
                  <div className="col">
                    <label>
                      <span>Amount (₹)</span>
                      <input
                        name="amount"
                        type="number"
                        value={txForm.amount}
                        onChange={onTxChange}
                        placeholder="2500"
                        required
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
                        <option value="food_online">Food delivery (Zomato, Swiggy)</option>
                        <option value="groceries">Groceries</option>
                        <option value="utilities">Utilities & bills</option>
                        <option value="fuel">Fuel</option>
                        <option value="travel">Travel</option>
                        <option value="entertainment">Entertainment</option>
                        <option value="cash">ATM cash withdrawal</option>
                        <option value="others">Others</option>
                      </select>
                    </label>
                  </div>

                  <div className="col">
                    <label>
                      <span>Description (optional)</span>
                      <input
                        name="description"
                        value={txForm.description}
                        onChange={onTxChange}
                        placeholder="e.g., Zomato dinner"
                      />
                    </label>
                  </div>
                </div>

                <button type="submit" disabled={loadingTx || !txForm.amount || parseFloat(txForm.amount) <= 0}>
                  {loadingTx ? "Adding..." : "Add dummy transaction"}
                </button>
              </form>

              <p className="muted" style={{ marginTop: 6 }}>
                Each transaction updates your behavioural features and triggers a fresh risk score.
              </p>
            </div>

            {/* 3. Recent Transactions */}
            <div className="card">
              <div className="card-header">Recent activity</div>
              {txs.length === 0 ? (
                <p className="muted">No spends yet. Add one above.</p>
              ) : (
                txs.slice(0, 10).map((t) => (
                  <div key={t.id || t._id || t.timestamp} className="dataset-row">
                    <div>
                      <div style={{ fontWeight: 500 }}>₹ {t.amount}</div>
                      <div className="muted">
                        {t.description || t.category} •{" "}
                        {t.timestamp ? new Date(t.timestamp).toLocaleString() : 'N/A'}
                      </div>
                    </div>
                    <div className="pill">{t.category}</div>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}