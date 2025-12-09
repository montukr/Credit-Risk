// src/pages/AdminOverviewPage.jsx
import React, { useEffect, useState, useRef } from "react";
import Layout from "../components/Layout";
import api from "../api";

export default function AdminOverviewPage() {
  const [loading, setLoading] = useState(true);
  const [customers, setCustomers] = useState([]);

  // expanded KPI card
  const [expandedCard, setExpandedCard] = useState(null);
  const [topData, setTopData] = useState([]);

  // click outside closing
  const wrapperRef = useRef(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get("/admin/customers");
        setCustomers(res.data || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // CLICK OUTSIDE HANDLER
  useEffect(() => {
    function handleClickOutside(e) {
      if (!expandedCard) return;
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setExpandedCard(null);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [expandedCard]);

  // Expansion handler
  const toggleCard = async (key, kind) => {
    if (expandedCard === key) {
      setExpandedCard(null);
      setTopData([]);
      return;
    }

    try {
      const res = await api.get("/admin/top/customers", { params: { kind } });
      setTopData(res.data.customers || []);
    } catch (e) {
      console.error(e);
      setTopData([]);
    }

    setExpandedCard(key);
  };

  // portfolio metrics
  const total = customers.length;
  const high = customers.filter((c) => c.risk_band === "High").length;
  const medium = customers.filter((c) => c.risk_band === "Medium").length;
  const low = customers.filter((c) => c.risk_band === "Low").length;

  // flagged = only High (matches backend)
  const flagged = high;

  const avg = (f) =>
    customers.length
      ? customers.reduce((a, c) => a + (Number(c[f]) || 0), 0) /
        customers.length
      : 0;

  const avgUtil = avg("UtilisationPct");
  const avgCash = avg("CashWithdrawalPct");
  const avgMix = avg("MerchantMixIndex");
  const avgRecentChange = avg("RecentSpendChangePct");

  return (
    <Layout>
      <h1>Portfolio overview</h1>
      <p className="page-caption">
        At-a-glance view of customer volumes, risk flags, and portfolio behaviour.
      </p>

      {loading && <p className="muted">Loading portfolio metrics…</p>}

      {/* KPI GRID */}
      <div
        className="grid-2"
        ref={wrapperRef}
        style={{ gap: 18, marginBottom: 20 }}
      >
        <KpiCard
          title="Total customers"
          subtitle="Active cardholders"
          value={total}
          bg="linear-gradient(135deg,#1d4ed8,#3b82f6)"
          cardKey="totalCustomers"
          kind="latest"
          expandedCard={expandedCard}
          toggle={toggleCard}
          topData={topData}
        />

        <KpiCard
          title="Flagged customers"
          subtitle="High risk"
          value={flagged}
          bg="linear-gradient(135deg,#b91c1c,#ef4444)"
          cardKey="flaggedCustomers"
          kind="flagged"
          expandedCard={expandedCard}
          toggle={toggleCard}
          topData={topData}
        />

        <KpiCard
          title="Average utilisation"
          subtitle="Spend vs limit"
          value={`${avgUtil.toFixed(1)}%`}
          bg="linear-gradient(135deg,#047857,#22c55e)"
          cardKey="avgUtilisation"
          kind="utilisation"
          expandedCard={expandedCard}
          toggle={toggleCard}
          topData={topData}
        />

        <KpiCard
          title="Average cash usage"
          subtitle="ATM / cash withdrawals"
          value={`${avgCash.toFixed(1)}%`}
          bg="linear-gradient(135deg,#7c2d12,#f97316)"
          cardKey="avgCash"
          kind="cash"
          expandedCard={expandedCard}
          toggle={toggleCard}
          topData={topData}
        />
      </div>

      {/* Risk + Behaviour sections */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">Risk band distribution</div>

          {total === 0 ? (
            <p className="muted">No customers yet.</p>
          ) : (
            <>
              {/* 3-band distribution bar */}
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
                <BarSegment flex={low} color="#38bdf8" />
                <BarSegment flex={medium} color="#eab308" />
                <BarSegment flex={high} color="#f97316" />
              </div>

              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <LegendPill label="Low" value={low} total={total} color="#38bdf8" />
                <LegendPill label="Medium" value={medium} total={total} color="#eab308" />
                <LegendPill label="High" value={high} total={total} color="#f97316" />
              </div>
            </>
          )}
        </div>

        <div className="card">
          <div className="card-header">Behavioural signals</div>
          {total === 0 ? (
            <p className="muted">No behavioural data.</p>
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
                hint="Average month-on-month spend change."
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
                hint="Interpretation of portfolio-level utilisation."
              />
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}

/*─────────────────────────────────────────────
  KPI CARD (EXPANDS IN PLACE)
─────────────────────────────────────────────*/
function KpiCard({
  title,
  subtitle,
  value,
  bg,
  cardKey,
  kind,
  expandedCard,
  toggle,
  topData,
}) {
  const expanded = expandedCard === cardKey;

  return (
    <div
      style={{
        background: bg,
        color: "white",
        padding: 16,
        borderRadius: 16,
        transition: "0.25s",
        boxShadow: "0 12px 30px rgba(0,0,0,0.25)",
        height: expanded ? "auto" : 130,
        opacity: expandedCard && !expanded ? 0.35 : 1,
        overflow: "hidden",
      }}
      onClick={(e) => expanded && e.stopPropagation()}
    >
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <span style={{ fontWeight: 600 }}>{title}</span>

        <button
          style={{
            border: "none",
            background: "rgba(255,255,255,0.28)",
            padding: "2px 6px",
            borderRadius: 999,
            color: "#fff",
            cursor: "pointer",
          }}
          onClick={(e) => {
            e.stopPropagation();
            toggle(cardKey, kind);
          }}
        >
          {expanded ? "▲" : "▼"}
        </button>
      </div>

      {/* VALUE */}
      <div style={{ fontSize: "2rem", marginTop: 4 }}>{value}</div>
      <div style={{ fontSize: "0.8rem", opacity: 0.9 }}>{subtitle}</div>

      {expanded && <ExpandedDetail title={title} list={topData} />}
    </div>
  );
}

/*─────────────────────────────────────────────
  EXPANDED CONTENT
─────────────────────────────────────────────*/
function ExpandedDetail({ title, list }) {
  return (
    <div
      style={{
        marginTop: 14,
        padding: 10,
        background: "rgba(255,255,255,0.15)",
        borderRadius: 10,
        backdropFilter: "blur(4px)",
      }}
    >
      <h4 style={{ marginBottom: 8, textAlign: "center" }}>{title} – Top 10</h4>

      {list.length === 0 ? (
        <p style={{ textAlign: "center" }}>No data available.</p>
      ) : (
        <table style={{ width: "100%", fontSize: "0.85rem" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "center" }}>User</th>
              <th style={{ textAlign: "center" }}>ID</th>
              <th style={{ textAlign: "center" }}>Util%</th>
              <th style={{ textAlign: "center" }}>Cash%</th>
              <th style={{ textAlign: "center" }}>Risk</th>
            </tr>
          </thead>
          <tbody>
            {list.map((c) => (
              <tr key={c.id}>
                <td style={{ textAlign: "center" }}>{c.username || "-"}</td>
                <td style={{ textAlign: "center" }}>{c.CustomerID}</td>
                <td style={{ textAlign: "center" }}>
                  {(c.UtilisationPct || 0).toFixed(1)}%
                </td>
                <td style={{ textAlign: "center" }}>
                  {(c.CashWithdrawalPct || 0).toFixed(1)}%
                </td>
                <td style={{ textAlign: "center" }}>{c.risk_band || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

/*─────────────────────────────────────────────
  SMALL COMPONENTS
─────────────────────────────────────────────*/
function BarSegment({ flex, color }) {
  if (!flex) return null;
  return <div style={{ flex, background: color }} />;
}

function LegendPill({ color, label, value, total }) {
  const pct = total ? ((value / total) * 100).toFixed(1) : 0;
  return (
    <div className="pill" style={{ display: "flex", gap: 4 }}>
      <span
        style={{
          width: 10,
          height: 10,
          borderRadius: 999,
          background: color,
        }}
      />
      {label}: {value} ({pct}%)
    </div>
  );
}

function BehaviourRow({ label, value, hint }) {
  return (
    <div
      style={{
        padding: 10,
        borderRadius: 12,
        background: "linear-gradient(135deg,#f8fafc,#e2e8f0)",
        border: "1px solid #cbd5e1",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <strong>{label}</strong>
        <span>{value}</span>
      </div>
      <div style={{ fontSize: "0.75rem", opacity: 0.7 }}>{hint}</div>
    </div>
  );
}
