import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Check,
  FileCheck2,
  Loader2,
  ScanLine,
  ScanText,
  Wand2,
} from "lucide-react";

const STAGES = [
  { key: "prep", label: "Enhance", icon: Wand2 },
  { key: "detect", label: "Detect", icon: ScanLine },
  { key: "classify", label: "Classify", icon: AlertTriangle },
  { key: "plates", label: "Read plates", icon: ScanText },
  { key: "evidence", label: "Evidence", icon: FileCheck2 },
];

export default function Pipeline({ analyzing, result }) {
  const [active, setActive] = useState(-1);

  useEffect(() => {
    if (!analyzing) {
      setActive(-1);
      return;
    }
    setActive(0);
    const id = setInterval(() => setActive((a) => (a + 1) % STAGES.length), 520);
    return () => clearInterval(id);
  }, [analyzing]);

  const stat = (key) => {
    if (!result) return null;
    const plates = result.violations.filter((v) => v.license_plate).length;
    return {
      prep: `${result.quality.score}/100`,
      detect: `${result.detections} users`,
      classify: `${result.violations.length} flags`,
      plates: `${plates} read`,
      evidence: "ready",
    }[key];
  };

  const done = result && !analyzing;

  return (
    <div className="pipeline">
      {STAGES.map((s, i) => {
        const isActive = analyzing && i === active;
        const Icon = done ? Check : isActive ? Loader2 : s.icon;
        return (
          <div
            key={s.key}
            className={`stage${done ? " done" : ""}${isActive ? " active" : ""}`}
          >
            <span className="stage-icon">
              <Icon size={16} strokeWidth={2} className={isActive ? "spin" : ""} />
            </span>
            <div className="stage-text">
              <span className="stage-label">{s.label}</span>
              <span className="stage-stat">{done ? stat(s.key) : " "}</span>
            </div>
            {i < STAGES.length - 1 && <span className="stage-link" />}
          </div>
        );
      })}
    </div>
  );
}
