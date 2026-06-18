const SEVERITY_CLASS = {
  HIGH: "badge danger",
  MEDIUM: "badge warning",
  LOW: "badge",
};

const label = (type) =>
  type.toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export default function ViolationCard({ violation }) {
  return (
    <article className="violation-card">
      <header>
        <h3>{label(violation.violation_type)}</h3>
        <span className={SEVERITY_CLASS[violation.severity] || "badge"}>
          {violation.severity}
        </span>
      </header>
      <dl>
        <div>
          <dt>Vehicle</dt>
          <dd>{violation.vehicle_type}</dd>
        </div>
        <div>
          <dt>Plate</dt>
          <dd>{violation.license_plate || "—"}</dd>
        </div>
        <div>
          <dt>Confidence</dt>
          <dd>{Math.round(violation.confidence * 100)}%</dd>
        </div>
      </dl>
    </article>
  );
}
