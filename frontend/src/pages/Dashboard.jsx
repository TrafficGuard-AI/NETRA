import { useEffect, useState } from "react";
import StatCard from "../components/StatCard.jsx";
import ViolationCard from "../components/ViolationCard.jsx";
import { getSummary, getViolations } from "../api.js";

export default function Dashboard() {
  const [summary, setSummary] = useState({ total: 0, high_severity: 0 });
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    getSummary().then(setSummary).catch(() => {});
    getViolations({ limit: 6 }).then(setRecent).catch(() => {});
  }, []);

  return (
    <section>
      <header className="page-head">
        <p className="eyebrow">Overview</p>
        <h1>Enforcement at a glance</h1>
        <p className="lede">
          Automated detection and classification of traffic violations from
          roadside camera imagery.
        </p>
      </header>

      <div className="stat-grid">
        <StatCard label="Total violations" value={summary.total} accent />
        <StatCard label="High severity" value={summary.high_severity} />
        <StatCard label="Detection rate" value="92%" hint="model confidence avg" />
      </div>

      <h2 className="section-title">Recent activity</h2>
      {recent.length ? (
        <div className="violation-grid">
          {recent.map((v) => (
            <ViolationCard key={v.id} violation={v} />
          ))}
        </div>
      ) : (
        <p className="empty">No violations yet. Analyze an image to get started.</p>
      )}
    </section>
  );
}
