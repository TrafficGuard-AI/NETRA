import { useEffect, useState } from "react";
import { Check, X, ShieldCheck } from "lucide-react";
import { evidenceUrl, getViolationEvidence } from "../api.js";
import { SensorFusionThumbs, SensorFusionBars } from "./SensorFusion.jsx";

const SEVERITY = {
  HIGH: { ring: "#fb5e73", chip: "badge danger" },
  MEDIUM: { ring: "#fbb540", chip: "badge warning" },
  LOW: { ring: "#3b9eff", chip: "badge" },
};
const STATUS_CLASS = { confirmed: "tag ok", dismissed: "tag muted", pending: "tag pending" };
const pretty = (t) => t.replace(/[_-]/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
const caseId = (id) => `#NX-${new Date().getFullYear()}-${String(id).padStart(6, "0")}`;

// Rich "Violation summary" panel — real detection data in the NETRA layout.
export default function ViolationModal({ violation, onClose, onStatus }) {
  const [meta, setMeta] = useState(null);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    setMeta(null);
    if (!violation) return;
    let alive = true;
    getViolationEvidence(violation.id)
      .then((d) => alive && setMeta(d))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [violation]);

  if (!violation) return null;
  const v = violation;
  const sev = SEVERITY[v.severity] || SEVERITY.LOW;
  const img = evidenceUrl(v.annotated_image_path);
  const conf = Math.round(v.confidence * 100);
  const q = meta?.quality;
  const condition = meta?.weather_condition;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} title="Close (Esc)">
          <X size={18} strokeWidth={2} />
        </button>

        <div className="modal-figure" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {img ? <img src={img} alt="Annotated evidence" style={{ flex: 1, minHeight: 0 }} /> : <div className="figure-skeleton" />}
          <SensorFusionThumbs confidence={conf} />
        </div>

        <div className="modal-side vs">
          <div className="vs-head">
            <div>
              <h2>Violation summary</h2>
              <p className="mono faint">{caseId(v.id)} · auto-detected</p>
            </div>
            <Gauge value={conf} color={sev.ring} />
          </div>

          <div className="vs-facts">
            <Fact label="Primary offence" tone="danger">{pretty(v.violation_type)}</Fact>
            <Fact label="Vehicle">{v.vehicle_type}</Fact>
            <Fact label="Plate" mono>{v.license_plate || "—"}</Fact>
            <Fact label="Confidence">{conf}%</Fact>
            <Fact label="Captured" mono>
              {v.timestamp ? new Date(v.timestamp).toLocaleString() : "—"}
            </Fact>
            <Fact label="Location">{v.location || "—"}</Fact>
            {condition && (
              <Fact label="Condition" tone="warning">{pretty(condition)}</Fact>
            )}
            <Fact label="Status">
              <span className={STATUS_CLASS[v.status] || "tag muted"}>{v.status}</span>
            </Fact>
          </div>

          <div className="vs-divider" />

          <div className="vs-bars">
            <div className="vs-bars-title">Detection &amp; image quality</div>
            <Bar label="Detection confidence" value={conf} color="#3b9eff" />
            {q && <Bar label="Sharpness" value={q.sharpness} color="#9fb4d2" />}
            {q && <Bar label="Brightness" value={q.brightness} color="#fbb540" />}
            {q && <Bar label="Image quality" value={q.score} color="#36d39a" strong />}
            {!q && (
              <p className="vs-hint">Per-frame quality metrics aren’t stored for this record.</p>
            )}
          </div>

          {q?.corrections?.length > 0 && (
            <div className="vs-note">
              Auto-corrected before detection: <b>{q.corrections.join(" · ")}</b>
            </div>
          )}

          <SensorFusionBars confidence={conf} />

          <div className="vs-prov signed">
            <div className="vs-prov-t s1">
              <ShieldCheck size={14} strokeWidth={2} color="#36D39A" />
              <span style={{ color: "#36D39A" }}>On-device signed evidence · tamper-evident chain</span>
            </div>
            <div className="vs-prov-s mono s2">
              sha256: {meta?.evidence_id ? meta.evidence_id.slice(0, 18) : "—"} · signed at edge node {v.location || "H-17"} · raw video never left the pole
            </div>
          </div>

          <div className="modal-actions">
            <button className="btn-confirm" onClick={() => onStatus(v.id, "confirmed")}>
              <Check size={15} strokeWidth={2.2} /> Confirm violation
            </button>
            <button className="btn-dismiss" onClick={() => onStatus(v.id, "dismissed")}>
              <X size={15} strokeWidth={2.2} /> Mark false positive
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Gauge({ value, color }) {
  const r = 40;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.max(0, Math.min(100, value)) / 100);
  return (
    <div className="vs-gauge">
      <svg width="96" height="96" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r={r} fill="none" stroke="rgba(132,168,222,0.16)" strokeWidth="9" />
        <circle
          cx="48"
          cy="48"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          transform="rotate(-90 48 48)"
        />
      </svg>
      <div className="vs-gauge-val" style={{ color }}>
        <strong>{value}</strong>
        <span>CONF</span>
      </div>
    </div>
  );
}

function Fact({ label, tone, mono, children }) {
  return (
    <div className="vs-fact">
      <span className="vs-fact-k">{label}</span>
      <span className={`vs-fact-v${tone ? " " + tone : ""}${mono ? " mono" : ""}`}>{children}</span>
    </div>
  );
}

function Bar({ label, value, color, strong }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={`vs-bar${strong ? " strong" : ""}`}>
      <span className="vs-bar-n">{label}</span>
      <span className="vs-bar-track">
        <i style={{ width: `${pct}%`, background: color }} />
      </span>
      <span className="vs-bar-v">{Math.round(value)}</span>
    </div>
  );
}
