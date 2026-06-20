import { useEffect, useRef, useState } from "react";
import { ChevronDown, Copy, Check, TerminalSquare } from "lucide-react";

// A terminal-style panel that "streams" the raw backend JSON line by line —
// surfaces real confidence scores and coordinates for technical credibility.
export default function RawOutput({ result }) {
  const [open, setOpen] = useState(true);
  const [shown, setShown] = useState(0);
  const [copied, setCopied] = useState(false);
  const bodyRef = useRef(null);

  const json = result ? JSON.stringify(result, null, 2) : "";
  const lines = json ? json.split("\n") : [];

  // Reveal lines progressively whenever a new result arrives.
  useEffect(() => {
    if (!result) return;
    setShown(0);
    const id = setInterval(() => {
      setShown((n) => {
        if (n >= lines.length) {
          clearInterval(id);
          return n;
        }
        return n + 1;
      });
    }, 28);
    return () => clearInterval(id);
  }, [json]); // eslint-disable-line react-hooks/exhaustive-deps

  // Keep the newest line in view while streaming.
  useEffect(() => {
    if (open && bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [shown, open]);

  if (!result) return null;

  const copy = () => {
    navigator.clipboard?.writeText(json);
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };

  const streaming = shown < lines.length;

  return (
    <div className={`raw${open ? " open" : ""}`}>
      <div className="raw-bar">
        <button className="raw-toggle" onClick={() => setOpen((o) => !o)}>
          <span className="raw-dots" aria-hidden>
            <i /><i /><i />
          </span>
          <TerminalSquare size={14} strokeWidth={1.9} />
          <span>API response</span>
          <span className="raw-meta">
            {streaming ? "streaming…" : `${lines.length} lines · ${json.length} bytes`}
          </span>
          <ChevronDown size={15} strokeWidth={2} className="raw-chevron" />
        </button>
        <button className="raw-copy" onClick={copy} title="Copy JSON">
          {copied ? <Check size={13} strokeWidth={2.2} /> : <Copy size={13} strokeWidth={1.9} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      {open && (
        <pre className="raw-body" ref={bodyRef}>
          <code>
            {lines.slice(0, shown).map((ln, i) => (
              <span key={i} className="raw-line">
                <span className="raw-ln">{i + 1}</span>
                <span className="raw-code">{ln || " "}</span>
              </span>
            ))}
            {streaming && <span className="raw-cursor" />}
          </code>
        </pre>
      )}
    </div>
  );
}
