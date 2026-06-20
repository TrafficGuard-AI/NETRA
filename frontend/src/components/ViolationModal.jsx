import { useEffect } from "react";
import { Check, X, MapPin, Gauge, Calendar } from "lucide-react";
import { evidenceUrl } from "../api.js";

const SEVERITY_CLASS = { HIGH: "badge danger", MEDIUM: "badge warning", LOW: "badge" };
const STATUS_CLASS = { confirmed: "tag ok", dismissed: "tag muted", pending: "tag pending" };
const pretty = (t) => t.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());

// Full-frame quick view of a single violation's annotated evidence.
export default function ViolationModal({ violation, onClose, onStatus }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!violation) return null;
  const v = violation;
  const img = evidenceUrl(v.annotated_image_path);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} title="Close (Esc)">
          <X size={18} strokeWidth={2} />
        </button>

        <div className="modal-figure">
          {img ? <img src={img} alt="Annotated evidence" /> : <div className="figure-skeleton" />}
        </div>

        <div className="modal-side">
          <div className="modal-head">
            <span className="mono faint">#{String(v.id).padStart(3, "0")}</span>
            <h2>{pretty(v.violation_type)}</h2>
            <div className="modal-tags">
              <span className={SEVERITY_CLASS[v.severity] || "badge"}>{v.severity}</span>
              <span className={STATUS_CLASS[v.status] || "tag muted"}>{v.status}</span>
            </div>
          </div>

          <dl className="modal-facts">
            <Fact label="Plate"><span className="mono">{v.license_plate || "—"}</span></Fact>
            <Fact label="Vehicle">{v.vehicle_type}</Fact>
            <Fact label="Confidence" icon={Gauge}>{Math.round(v.confidence * 100)}%</Fact>
            <Fact label="Location" icon={MapPin}>{v.location || "—"}</Fact>
            <Fact label="Captured" icon={Calendar}>
              {v.timestamp ? new Date(v.timestamp).toLocaleString() : "—"}
            </Fact>
          </dl>

          <div className="modal-actions">
            <button className="btn-confirm" onClick={() => onStatus(v.id, "confirmed")}>
              <Check size={15} strokeWidth={2.2} /> Confirm
            </button>
            <button className="btn-dismiss" onClick={() => onStatus(v.id, "dismissed")}>
              <X size={15} strokeWidth={2.2} /> Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Fact({ label, icon: Icon, children }) {
  return (
    <div className="fact">
      <dt>
        {Icon && <Icon size={13} strokeWidth={1.8} />}
        {label}
      </dt>
      <dd>{children}</dd>
    </div>
  );
}
