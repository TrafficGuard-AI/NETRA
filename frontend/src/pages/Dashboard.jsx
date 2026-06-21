import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, AlertOctagon, ArrowRight, Gauge, ShieldAlert } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import StatCard from "../components/StatCard.jsx";
import ViolationCard from "../components/ViolationCard.jsx";
import Donut, { COLORS } from "../components/Donut.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { getByType, getRules, getSummary, getViolations } from "../api.js";

const pretty = (t) => t.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());

const RULE_STATUS = {
  active: { label: "Active", cls: "ok" },
  "needs-weight": { label: "Needs weight", cls: "pending" },
  "needs-config": { label: "Needs config", cls: "pending" },
  planned: { label: "Planned", cls: "muted" },
};

export default function Dashboard() {
  const [summary, setSummary] = useState({ total: 0, high_severity: 0, avg_confidence: 0, today: 0 });
  const [byType, setByType] = useState([]);
  const [recent, setRecent] = useState([]);
  const [rules, setRules] = useState([]);

  useEffect(() => {
    getSummary().then(setSummary).catch(() => {});
    getByType()
      .then((r) => setByType(r.map((x) => ({ name: pretty(x.type), value: x.count }))))
      .catch(() => {});
    getViolations({ limit: 4 }).then(setRecent).catch(() => {});
    getRules().then(setRules).catch(() => {});
  }, []);

  const activeCount = rules.filter((r) => r.status === "active").length;

  return (
    <section>
      <PageHeader
        eyebrow="Overview"
        title="Enforcement at a glance"
        lede="Automated detection and classification of traffic violations from roadside camera imagery — every flagged event scored and stored as evidence."
      />

      <div className="stat-grid">
        <StatCard label="Total violations" value={summary.total} icon={AlertOctagon} accent />
        <StatCard label="High severity" value={summary.high_severity} icon={ShieldAlert} />
        <StatCard
          label="Avg. confidence"
          value={summary.total ? Math.round(summary.avg_confidence * 100) : null}
          suffix="%"
          icon={Gauge}
        />
        <StatCard label="Violations today" value={summary.today} icon={Activity} />
      </div>

      <div className="split">
        <div className="card panel">
          <div className="panel-head">
            <h2>Violation mix</h2>
            <span className="panel-sub">by category</span>
          </div>
          {byType.length ? (
            <div className="mix">
              <Donut data={byType} total={summary.total} />
              <ul className="legend">
                {byType.map((d, i) => (
                  <li key={d.name}>
                    <span className="dot" style={{ background: COLORS[i % COLORS.length] }} />
                    {d.name}
                    <strong>{d.value}</strong>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <EmptyState icon={Gauge} title="No data yet" hint="Analyze a frame to populate the mix." />
          )}
        </div>

        <div className="card panel highlight">
          <div className="panel-head">
            <h2>Get started</h2>
          </div>
          <p className="panel-copy">
            Upload a junction snapshot and NETRA will preprocess it, detect
            road users, flag violations and read plates — in one pass.
          </p>
          <Link to="/analyze" className="btn-primary lg">
            Analyze an image <ArrowRight size={16} strokeWidth={2} />
          </Link>
        </div>
      </div>

      {rules.length > 0 && (
        <>
          <div className="section-head">
            <h2>Detection coverage</h2>
            <span className="panel-sub">{activeCount} of {rules.length} rules active</span>
          </div>
          <div className="coverage">
            {rules.map((r) => {
              const s = RULE_STATUS[r.status] || RULE_STATUS.planned;
              return (
                <div key={r.code} className="coverage-item">
                  <span className="coverage-name">{r.name}</span>
                  <span className={`tag ${s.cls}`}>{s.label}</span>
                </div>
              );
            })}
          </div>
        </>
      )}

      <div className="section-head">
        <h2>Recent activity</h2>
        <Link to="/violations" className="link-more">
          View all <ArrowRight size={14} strokeWidth={2} />
        </Link>
      </div>
      {recent.length ? (
        <div className="violation-grid">
          {recent.map((v) => (
            <ViolationCard key={v.id} violation={v} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={AlertOctagon}
          title="No violations recorded"
          hint="Analyze your first image to see flagged events here."
        />
      )}
    </section>
  );
}
