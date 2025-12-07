import React, { useState } from "react";
import api from "../api";

export default function AdminRiskLabPage() {
  const [form, setForm] = useState({
    credit_limit: 100000,
    utilisation_pct: 60,
    avg_payment_ratio: 70,
    min_due_paid_freq: 20,
    merchant_mix_index: 0.6,
    cash_withdrawal_pct: 0,
    recent_spend_change_pct: 0,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({
      ...f,
      [name]: parseFloat(value),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await api.post("/risk/score_row", form);
      setResult(res.data);
    } catch (err) {
      alert(err?.response?.data?.detail || "Scoring failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-root">
      <div className="app-main">

        <h1>Risk Lab</h1>
        <p className="page-caption">
          Simulate behavioural scenarios and see delinquency risk, rule triggers, and outreach suggestions.
        </p>

        {/* Input Feature Form */}
        <div className="card">
          <div className="card-header">Input behaviour features</div>

          <form onSubmit={handleSubmit}>
            <div className="row">
              {/* Column 1 */}
              <div className="col">
                <label>
                  <span>Credit limit (₹)</span>
                  <input
                    name="credit_limit"
                    type="number"
                    value={form.credit_limit}
                    onChange={onChange}
                  />
                </label>

                <label>
                  <span>Utilisation %</span>
                  <input
                    name="utilisation_pct"
                    type="number"
                    value={form.utilisation_pct}
                    onChange={onChange}
                  />
                </label>

                <label>
                  <span>Avg payment ratio %</span>
                  <input
                    name="avg_payment_ratio"
                    type="number"
                    value={form.avg_payment_ratio}
                    onChange={onChange}
                  />
                </label>

                <label>
                  <span>Min due paid frequency %</span>
                  <input
                    name="min_due_paid_freq"
                    type="number"
                    value={form.min_due_paid_freq}
                    onChange={onChange}
                  />
                </label>
              </div>

              {/* Column 2 */}
              <div className="col">
                <label>
                  <span>Merchant mix index (0-1)</span>
                  <input
                    name="merchant_mix_index"
                    type="number"
                    step="0.01"
                    value={form.merchant_mix_index}
                    onChange={onChange}
                  />
                </label>

                <label>
                  <span>Cash withdrawal %</span>
                  <input
                    name="cash_withdrawal_pct"
                    type="number"
                    value={form.cash_withdrawal_pct}
                    onChange={onChange}
                  />
                </label>

                <label>
                  <span>Recent spend change %</span>
                  <input
                    name="recent_spend_change_pct"
                    type="number"
                    value={form.recent_spend_change_pct}
                    onChange={onChange}
                  />
                </label>
              </div>
            </div>

            <button type="submit" disabled={loading}>
              {loading ? "Scoring..." : "Score scenario"}
            </button>
          </form>
        </div>

        {/* Result Section */}
        {result && (
          <div className="card">
            <div className="card-header">Result</div>

            <p>
              Ensemble probability:{" "}
              <strong>{(result.ensemble_probability * 100).toFixed(1)}%</strong>
            </p>

            <p>
              Risk band: <strong>{result.risk_band}</strong>
            </p>

            {result.rules && result.rules.length > 0 && (
              <>
                <h4>Early warning signals</h4>

                {result.rules.map((r) => (
                  <div key={r.rule_name} className="dataset-row">
                    <div>
                      <strong>{r.rule_name}</strong>
                      <p className="muted">{r.reason}</p>
                    </div>

                    <div className="pill">
                      Suggested: {r.suggested_outreach}
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
