import { useEffect, useState } from "react";
import { getViolations } from "../api.js";

const TYPES = ["", "TRIPLE_RIDING", "HELMET_NON_COMPLIANCE"];

export default function Violations() {
  const [rows, setRows] = useState([]);
  const [type, setType] = useState("");

  useEffect(() => {
    getViolations({ type: type || undefined, limit: 100 })
      .then(setRows)
      .catch(() => setRows([]));
  }, [type]);

  return (
    <section>
      <header className="page-head">
        <p className="eyebrow">Records</p>
        <h1>Violation register</h1>
        <p className="lede">Every flagged event, searchable and exportable.</p>
      </header>

      <div className="toolbar">
        <select value={type} onChange={(e) => setType(e.target.value)}>
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {t ? t.replace(/_/g, " ") : "All types"}
            </option>
          ))}
        </select>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Vehicle</th>
            <th>Plate</th>
            <th>Confidence</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((v) => (
            <tr key={v.id}>
              <td className="mono">#{v.id}</td>
              <td>{v.violation_type.replace(/_/g, " ")}</td>
              <td>{v.severity}</td>
              <td>{v.vehicle_type}</td>
              <td className="mono">{v.license_plate || "—"}</td>
              <td>{Math.round(v.confidence * 100)}%</td>
              <td>{v.status}</td>
            </tr>
          ))}
          {!rows.length && (
            <tr>
              <td colSpan={7} className="empty-cell">
                No records found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
