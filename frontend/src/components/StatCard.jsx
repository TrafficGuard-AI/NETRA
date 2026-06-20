import { useCountUp } from "../hooks/useCountUp.js";

export default function StatCard({ label, value, suffix = "", icon: Icon, accent }) {
  const isNum = typeof value === "number";
  const animated = useCountUp(isNum ? value : 0);
  return (
    <div className={`stat-card${accent ? " is-accent" : ""}`}>
      {Icon && (
        <span className="stat-icon">
          <Icon size={18} strokeWidth={1.75} />
        </span>
      )}
      <span className="stat-label">{label}</span>
      <span className="stat-value">
        {isNum ? animated : value ?? "—"}
        {isNum && suffix ? <em className="stat-suffix">{suffix}</em> : null}
      </span>
    </div>
  );
}
