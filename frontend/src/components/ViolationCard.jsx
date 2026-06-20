import { AlertTriangle, Bike, Car, Clock } from "lucide-react";

const SEVERITY_CLASS = {
  HIGH: "badge danger",
  MEDIUM: "badge warning",
  LOW: "badge",
};

const label = (type) =>
  type.toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

const vehicleIcon = (type) => (type === "Two-Wheeler" ? Bike : Car);

const when = (ts) => {
  if (!ts) return "—";
  return new Date(ts).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export default function ViolationCard({ violation }) {
  const VIcon = vehicleIcon(violation.vehicle_type);
  const pct = Math.round(violation.confidence * 100);

  return (
    <article className="violation-card">
      <header>
        <span className="violation-glyph">
          <AlertTriangle size={16} strokeWidth={2} />
        </span>
        <h3>{label(violation.violation_type)}</h3>
        <span className={SEVERITY_CLASS[violation.severity] || "badge"}>
          {violation.severity}
        </span>
      </header>

      <div className="violation-row">
        <VIcon size={15} strokeWidth={1.75} />
        <span>{violation.vehicle_type}</span>
        <span className="plate">{violation.license_plate || "No plate"}</span>
      </div>

      <div className="confidence">
        <div className="confidence-track">
          <span className="confidence-fill" style={{ width: `${pct}%` }} />
        </div>
        <span className="confidence-pct">{pct}%</span>
      </div>

      <footer className="violation-foot">
        <Clock size={13} strokeWidth={1.75} />
        {when(violation.timestamp)}
      </footer>
    </article>
  );
}
