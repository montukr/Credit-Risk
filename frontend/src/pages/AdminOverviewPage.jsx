// src/pages/AdminOverviewPage.jsx
import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api";

export default function AdminOverviewPage() {
  const [loading, setLoading] = useState(true);
  const [customers, setCustomers] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get("/admin/customers");
        setCustomers(res.data || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const total = customers.length;
  const high = customers.filter((c) => c.risk_band === "High").length;
  const med = customers.filter((c) => c.risk_band === "Medium").length;
  const low = customers.filter((c) => c.risk_band === "Low").length;
  const veryLow = customers.filter((c) => c.risk_band === "Very Low").length;
  const critical = customers.filter((c) => c.risk_band === "Critical").length;
  const flagged = high + med + critical;

  const avg = (field) => {
    if (!customers.length) return 0;
    const s = customers.reduce(
      (acc, c) => acc + (Number(c[field]) || 0),
      0
    );
    return s / customers.length;
  };

  const avgUtil = avg("UtilisationPct");
  const avgCash = avg("CashWithdrawalPct");
  const avgMix = avg("MerchantMixIndex");
  const avgRecentChange = avg("RecentSpendChangePct");

  return (
    <Layout>
      <h1>Portfolio overview</h1>
      <p className="page-caption">
        At‑a‑glance view of customer volumes, risk flags, and portfolio behaviour.
      </p>

      {loading && <p className="muted">Loading portfolio metrics…</p>}

      {/* 2×2 KPI grid */}
      <div className="grid-2">
        <KpiCard
          title="Total customers"
          value={total}
          subtitle="Active cardholders"
          bg="linear-gradient(135deg,#1d4ed8,#3b82f6)"
        />
        <KpiCard
          title="Flagged customers"
          value={flagged}
          subtitle="High / Medium / Critical"
          bg="linear-gradient(135deg,#b91c1c,#ef4444)"
        />
        <KpiCard
          title="Average utilisation"
          value={`${avgUtil.toFixed(1)}%`}
          subtitle="Spend vs limit"
          bg="linear-gradient(135deg,#047857,#22c55e)"
        />
        <KpiCard
          title="Average cash usage"
          value={`${avgCash.toFixed(1)}%`}
          subtitle="ATM / cash withdrawals"
          bg="linear-gradient(135deg,#7c2d12,#f97316)"
        />
      </div>

      {/* 2‑column: Risk vs Behaviour */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">Risk band distribution</div>
          {total === 0 ? (
            <p className="muted">No customers yet. Upload or simulate data first.</p>
          ) : (
            <>
              <div
                style={{
                  display: "flex",
                  height: 26,
                  borderRadius: 999,
                  overflow: "hidden",
                  border: "1px solid rgba(148,163,184,0.7)",
                  marginBottom: 10,
                }}
              >
                <BarSegment flex={veryLow} color="#22c55e" />
                <BarSegment flex={low} color="#38bdf8" />
                <BarSegment flex={med} color="#eab308" />
                <BarSegment flex={high} color="#f97316" />
                <BarSegment flex={critical} color="#ef4444" />
              </div>

              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 8,
                  fontSize: "0.8rem",
                }}
              >
                <LegendPill color="#22c55e" label="Very Low" value={veryLow} total={total} />
                <LegendPill color="#38bdf8" label="Low" value={low} total={total} />
                <LegendPill color="#eab308" label="Medium" value={med} total={total} />
                <LegendPill color="#f97316" label="High" value={high} total={total} />
                <LegendPill color="#ef4444" label="Critical" value={critical} total={total} />
              </div>
            </>
          )}
        </div>

        <div className="card">
          <div className="card-header">Behavioural signals</div>
          {total === 0 ? (
            <p className="muted">No behavioural data yet.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <BehaviourRow
                label="Merchant mix index"
                value={avgMix.toFixed(2)}
                hint="Higher = more diversified spending across merchants."
              />
              <BehaviourRow
                label="Recent spend change"
                value={`${avgRecentChange.toFixed(1)}%`}
                hint="Average month‑on‑month spend change across the book."
              />
              <BehaviourRow
                label="Utilisation profile"
                value={
                  avgUtil > 70
                    ? "Aggressive utilisation portfolio"
                    : avgUtil > 30
                    ? "Balanced utilisation portfolio"
                    : "Low utilisation portfolio"
                }
                hint="Interpretation of portfolio‑level utilisation."
              />
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}

function KpiCard({ title, value, subtitle, bg }) {
  return (
    <div
      className="card kpi-card"
      style={{
        background: bg,
        color: "#ffffff",
        boxShadow: "0 18px 40px rgba(15,23,42,0.4)",
        border: "1px solid rgba(148,163,184,0.4)",
      }}
    >
      <div className="card-header" style={{ color: "#e5e7eb" }}>
        {title}
      </div>
      <p
        className="kpi-number"
        style={{ fontSize: "1.6rem", fontWeight: 650, marginBottom: 4 }}
      >
        {value}
      </p>
      <p
        className="muted"
        style={{ color: "rgba(226,232,240,0.9)", fontSize: "0.8rem" }}
      >
        {subtitle}
      </p>
    </div>
  );
}

function BarSegment({ flex, color }) {
  if (!flex) return null;
  return (
    <div
      style={{
        flex,
        background: color,
      }}
    />
  );
}

function LegendPill({ color, label, value, total }) {
  if (!total) return null;
  const pct = ((value / total) * 100).toFixed(1);
  return (
    <div
      className="pill"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        background: "#ffffff",
      }}
    >
      <span
        style={{
          width: 10,
          height: 10,
          borderRadius: 999,
          background: color,
          border: "1px solid rgba(148,163,184,0.7)",
        }}
      />
      <span>
        {label}: {value} ({pct}%)
      </span>
    </div>
  );
}

function BehaviourRow({ label, value, hint }) {
  return (
    <div
      style={{
        padding: "8px 10px",
        borderRadius: 12,
        background: "linear-gradient(135deg,#f9fafb,#e5e7eb)",
        border: "1px solid rgba(148,163,184,0.6)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: 2,
        }}
      >
        <span style={{ fontSize: "0.86rem", fontWeight: 600 }}>{label}</span>
        <span style={{ fontSize: "0.9rem" }}>{value}</span>
      </div>
      <div className="muted" style={{ fontSize: "0.75rem" }}>
        {hint}
      </div>
    </div>
  );
}
