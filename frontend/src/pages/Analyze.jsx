import { useState } from "react";
import { CheckCircle2, Clock, MapPin, Users, Wand2, XCircle } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import UploadPanel from "../components/UploadPanel.jsx";
import ViolationCard from "../components/ViolationCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import Pipeline from "../components/Pipeline.jsx";
import RawOutput from "../components/RawOutput.jsx";
import { API_ORIGIN, uploadImage, uploadVideo } from "../api.js";

export default function Analyze() {
  const [items, setItems] = useState([]);
  const [location, setLocation] = useState("");
  const [running, setRunning] = useState(false);

  const patch = (id, fields) =>
    setItems((cur) => cur.map((it) => (it.id === id ? { ...it, ...fields } : it)));

  const analyzeFiles = async (files) => {
    // Release any previous object URLs before starting a fresh batch.
    items.forEach((it) => it.previewUrl && URL.revokeObjectURL(it.previewUrl));

    const queued = files.map((file, i) => ({
      id: `${Date.now()}-${i}-${file.name}`,
      file,
      name: file.name,
      mediaType: file.type.startsWith("video/") ? "video" : "image",
      previewUrl: URL.createObjectURL(file),
      status: "pending", // pending | analyzing | done | error
      result: null,
      error: null,
    }));
    setItems(queued);
    setRunning(true);

    // Sequential — one request at a time so the backend (and the UI) aren't
    // overwhelmed, and progress is visible per file.
    for (const item of queued) {
      patch(item.id, { status: "analyzing" });
      try {
        const result =
          item.mediaType === "video"
            ? await uploadVideo(item.file, location)
            : await uploadImage(item.file, location);
        patch(item.id, { status: "done", result });
      } catch {
        patch(item.id, { status: "error", error: "Analysis failed — is the backend running?" });
      }
    }
    setRunning(false);
  };

  const done = items.filter((it) => it.status === "done");
  const totalViolations = done.reduce((n, it) => n + it.result.violations.length, 0);

  return (
    <section>
      <PageHeader
        eyebrow="Analyze"
        title="Inspect traffic media"
        lede="Upload one or more images or videos — each is preprocessed, detected and classified in turn."
      />

      <label className="field">
        <MapPin size={15} strokeWidth={1.75} />
        <input
          placeholder="Camera location (e.g. Dadar TT Junction)"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
      </label>

      <UploadPanel onFiles={analyzeFiles} busy={running} />

      {items.length > 0 && (
        <div className="batch-bar rise">
          <span>
            <strong>{done.length}</strong> of {items.length} analyzed
          </span>
          {done.length > 0 && (
            <span className={totalViolations > 0 ? "batch-flag alert" : "batch-flag"}>
              {totalViolations} violation{totalViolations === 1 ? "" : "s"} total
            </span>
          )}
        </div>
      )}

      {items.map((item, i) => (
        <AnalysisItem key={item.id} item={item} index={i} total={items.length} />
      ))}
    </section>
  );
}

function AnalysisItem({ item, index, total }) {
  const STATUS = {
    pending: { icon: Clock, cls: "muted", text: "Queued" },
    analyzing: { icon: null, cls: "pending", text: "Analyzing…" },
    done: { icon: CheckCircle2, cls: "ok", text: "Done" },
    error: { icon: XCircle, cls: "danger", text: "Failed" },
  }[item.status];

  return (
    <div className="analysis-item rise">
      <div className="analysis-head">
        <span className="analysis-index">{total > 1 ? `${index + 1}/${total}` : ""}</span>
        <span className="analysis-name" title={item.name}>{item.name}</span>
        <span className={`tag ${STATUS.cls}`}>{STATUS.text}</span>
      </div>

      {item.status === "analyzing" && <Pipeline analyzing result={null} />}
      {item.status === "error" && <div className="dropzone-error">{item.error}</div>}
      {item.status === "done" && item.result && <ResultCard item={item} />}
    </div>
  );
}

function ResultCard({ item }) {
  const result = item.result;
  return (
    <div className="result">
      <div className="result-meta">
        <StatChip label="Image quality" value={`${result.quality.score}`} suffix="/100" />
        <StatChip label="Road users" value={result.detections} />
        <StatChip label="Violations" value={result.violations.length} alert={result.violations.length > 0} />
        {result.media_type === "video" && (
          <StatChip label="Frames sampled" value={result.frames_processed} />
        )}
        {result.media_type === "video" && result.duration_seconds != null && (
          <StatChip label="Duration" value={result.duration_seconds} suffix="s" />
        )}
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
        <Figure
          caption={item.mediaType === "video" ? "Original video" : "Original"}
          media={{ url: item.previewUrl, mediaType: item.mediaType }}
        />
        <Figure
          caption="Annotated evidence"
          media={result.evidence_url ? { url: `${API_ORIGIN}${result.evidence_url}`, mediaType: "image" } : null}
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

function Figure({ caption, media, accent }) {
  return (
    <figure className={`figure${accent ? " accent" : ""}`}>
      <div className="figure-frame">
        {media?.url && media.mediaType === "video" ? (
          <video src={media.url} controls muted playsInline />
        ) : media?.url ? (
          <img src={media.url} alt={caption} />
        ) : (
          <div className="figure-skeleton" />
        )}
      </div>
      <figcaption>{caption}</figcaption>
    </figure>
  );
}
