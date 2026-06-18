export default function StatCard({ label, value, hint, accent }) {
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      <span className="stat-value" style={accent ? { color: "var(--accent)" } : undefined}>
        {value}
      </span>
      {hint && <span className="stat-hint">{hint}</span>}
    </div>
  );
}
