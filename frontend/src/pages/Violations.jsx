import { useEffect, useMemo, useState } from "react";
import { Check, ImageOff, ListChecks, Search, X } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ViolationModal from "../components/ViolationModal.jsx";
import { evidenceUrl, getViolations, updateViolationStatus } from "../api.js";

const TYPES = ["", "TRIPLE_RIDING", "HELMET_NON_COMPLIANCE"];
const SEVERITY_CLASS = { HIGH: "badge danger", MEDIUM: "badge warning", LOW: "badge" };
const STATUS_CLASS = { confirmed: "tag ok", dismissed: "tag muted", pending: "tag pending" };
const pretty = (t) => t.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());

export default function Violations() {
  const [rows, setRows] = useState([]);
  const [type, setType] = useState("");
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(null);

  useEffect(() => {
    getViolations({ type: type || undefined, limit: 100 })
      .then(setRows)
      .catch(() => setRows([]));
  }, [type]);

  const setStatus = async (id, status) => {
    const updated = await updateViolationStatus(id, status);
    setRows((rs) => rs.map((r) => (r.id === id ? updated : r)));
    setActive((a) => (a && a.id === id ? updated : a));
  };

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter(
      (v) =>
        (v.license_plate || "").toLowerCase().includes(q) ||
        v.vehicle_type.toLowerCase().includes(q) ||
        v.violation_type.toLowerCase().includes(q)
    );
  }, [rows, query]);

  return (
    <section>
      <PageHeader
        eyebrow="Records"
        title="Violation register"
        lede="Every flagged event, searchable and ready for review."
      />

      <div className="toolbar">
        <div className="search">
          <Search size={16} strokeWidth={1.75} />
          <input
            placeholder="Search plate, vehicle or type…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <select value={type} onChange={(e) => setType(e.target.value)}>
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {t ? pretty(t) : "All types"}
            </option>
          ))}
        </select>
        <span className="count-pill">{filtered.length} records</span>
      </div>

      <div className="table-wrap card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th aria-label="Evidence"></th>
              <th>Type</th>
              <th>Severity</th>
              <th>Vehicle</th>
              <th>Plate</th>
              <th>Location</th>
              <th>Confidence</th>
              <th>Status</th>
              <th>Review</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((v) => (
              <tr
                key={v.id}
                className={`row-clickable${v.status === "dismissed" ? " is-dismissed" : ""}`}
                onClick={() => setActive(v)}
              >
                <td className="mono faint">#{String(v.id).padStart(3, "0")}</td>
                <td>
                  <Thumb v={v} />
                </td>
                <td className="strong">{pretty(v.violation_type)}</td>
                <td>
                  <span className={SEVERITY_CLASS[v.severity] || "badge"}>{v.severity}</span>
                </td>
                <td>{v.vehicle_type}</td>
                <td className="mono">{v.license_plate || "—"}</td>
                <td className="faint">{v.location || "—"}</td>
                <td>{Math.round(v.confidence * 100)}%</td>
                <td>
                  <span className={STATUS_CLASS[v.status] || "tag muted"}>{v.status}</span>
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  <div className="row-actions">
                    <button
                      className="icon-btn confirm"
                      title="Confirm"
                      onClick={() => setStatus(v.id, "confirmed")}
                    >
                      <Check size={15} strokeWidth={2.2} />
                    </button>
                    <button
                      className="icon-btn dismiss"
                      title="Dismiss"
                      onClick={() => setStatus(v.id, "dismissed")}
                    >
                      <X size={15} strokeWidth={2.2} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!filtered.length && (
          <EmptyState icon={ListChecks} title="No matching records" hint="Try a different search or filter." />
        )}
      </div>

      <ViolationModal violation={active} onClose={() => setActive(null)} onStatus={setStatus} />
    </section>
  );
}

function Thumb({ v }) {
  const [broken, setBroken] = useState(false);
  const src = evidenceUrl(v.annotated_image_path);
  if (!src || broken) {
    return (
      <span className="thumb thumb-empty">
        <ImageOff size={15} strokeWidth={1.7} />
      </span>
    );
  }
  return (
    <span className="thumb">
      <img src={src} alt="" loading="lazy" onError={() => setBroken(true)} />
    </span>
  );
}
