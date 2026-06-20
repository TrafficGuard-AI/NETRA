import { useState } from "react";
import { CheckCircle2, MapPin, Users, Wand2 } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import UploadPanel from "../components/UploadPanel.jsx";
import ViolationCard from "../components/ViolationCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import Pipeline from "../components/Pipeline.jsx";
import RawOutput from "../components/RawOutput.jsx";
import { API_ORIGIN } from "../api.js";

export default function Analyze() {
  const [result, setResult] = useState(null);
  const [preview, setPreview] = useState(null);
  const [location, setLocation] = useState("");
  const [analyzing, setAnalyzing] = useState(false);

  return (
    <section>
      <PageHeader
        eyebrow="Analyze"
        title="Inspect a single frame"
        lede="Upload a traffic image to run preprocessing, detection and violation classification in one pass."
      />

      <label className="field">
        <MapPin size={15} strokeWidth={1.75} />
        <input
          placeholder="Camera location (e.g. Dadar TT Junction)"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
      </label>

      <UploadPanel
        onStart={() => {
          setAnalyzing(true);
          setResult(null);
        }}
        onResult={(r) => {
          setResult(r);
          setAnalyzing(false);
        }}
        onPreview={setPreview}
        location={location}
      />

      <Pipeline analyzing={analyzing} result={result} />

      {result && (
        <div className="result rise">
          <div className="result-meta">
            <StatChip label="Image quality" value={`${result.quality.score}`} suffix="/100" />
            <StatChip label="Road users" value={result.detections} />
            <StatChip label="Violations" value={result.violations.length} alert={result.violations.length > 0} />
          </div>

          {result.quality.corrections.length > 0 && (
            <div className="corrections">
              <Wand2 size={14} strokeWidth={1.75} />
              <span>Auto-corrected:</span>
              {result.quality.corrections.map((c) => (
                <span key={c} className="correction-chip">{c}</span>
              ))}
            </div>
          )}

          {result.road_users.length > 0 && (
            <div className="detected">
              <Users size={14} strokeWidth={1.75} />
              <span>Road users:</span>
              {result.road_users.map((r) => (
                <span key={r.category} className="detected-chip">
                  <strong>{r.count}</strong> {r.category}
                </span>
              ))}
            </div>
          )}

          <div className="compare">
            <Figure caption="Original" src={preview} />
            <Figure
              caption="Annotated evidence"
              src={result.evidence_url ? `${API_ORIGIN}${result.evidence_url}` : null}
              accent
            />
          </div>

          <div className="section-head">
            <h2>Detected violations</h2>
          </div>
          {result.violations.length ? (
            <div className="violation-grid">
              {result.violations.map((v) => (
                <ViolationCard key={v.id} violation={v} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={CheckCircle2}
              title="No violations detected"
              hint="All road users in this frame appear compliant."
            />
          )}

          <RawOutput result={result} />
        </div>
      )}
    </section>
  );
}

function StatChip({ label, value, suffix, alert }) {
  return (
    <div className={`chip${alert ? " alert" : ""}`}>
      <span>{label}</span>
      <strong>
        {value}
        {suffix && <em>{suffix}</em>}
      </strong>
    </div>
  );
}

function Figure({ caption, src, accent }) {
  return (
    <figure className={`figure${accent ? " accent" : ""}`}>
      <div className="figure-frame">
        {src ? <img src={src} alt={caption} /> : <div className="figure-skeleton" />}
      </div>
      <figcaption>{caption}</figcaption>
    </figure>
  );
}
