import { useState } from "react";
import UploadPanel from "../components/UploadPanel.jsx";
import ViolationCard from "../components/ViolationCard.jsx";

const API_ORIGIN = (import.meta.env.VITE_API_URL || "http://localhost:8000/api").replace(/\/api$/, "");

export default function Analyze() {
  const [result, setResult] = useState(null);

  return (
    <section>
      <header className="page-head">
        <p className="eyebrow">Analyze</p>
        <h1>Inspect a single frame</h1>
        <p className="lede">
          Upload a traffic image to run preprocessing, detection and violation
          classification in one pass.
        </p>
      </header>

      <UploadPanel onResult={setResult} />

      {result && (
        <div className="result">
          <div className="result-meta">
            <StatChip label="Quality" value={`${result.quality_score}/100`} />
            <StatChip label="Detections" value={result.detections} />
            <StatChip label="Violations" value={result.violations.length} />
          </div>

          {result.evidence_url && (
            <figure className="evidence">
              <img src={`${API_ORIGIN}${result.evidence_url}`} alt="Annotated evidence" />
              <figcaption>Annotated evidence</figcaption>
            </figure>
          )}

          <div className="violation-grid">
            {result.violations.map((v) => (
              <ViolationCard key={v.id} violation={v} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function StatChip({ label, value }) {
  return (
    <div className="chip">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
