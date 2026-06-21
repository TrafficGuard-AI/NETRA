import { useRef, useState } from "react";
import { ImageUp, Loader2 } from "lucide-react";

// Thin multi-file picker. The parent owns the sequential analysis loop and all
// per-file state; this just collects the chosen files and hands them up.
export default function UploadPanel({ onFiles, busy }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const pick = (fileList) => {
    const files = Array.from(fileList || []);
    if (files.length) onFiles(files);
  };

  return (
    <div
      className={`dropzone${dragging ? " is-dragging" : ""}${busy ? " is-busy" : ""}`}
      onClick={() => !busy && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        if (!busy) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        if (!busy) pick(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*,video/*"
        multiple
        hidden
        onChange={(e) => {
          pick(e.target.files);
          e.target.value = ""; // allow re-selecting the same files
        }}
      />
      <span className="dropzone-icon">
        {busy ? (
          <Loader2 size={26} strokeWidth={1.75} className="spin" />
        ) : (
          <ImageUp size={26} strokeWidth={1.5} />
        )}
      </span>
      <p className="dropzone-title">
        {busy ? "Analyzing media…" : "Drop images or videos, or click to browse"}
      </p>
      <span className="dropzone-hint">
        JPG, PNG or MP4/MOV · select multiple — analyzed one by one
      </span>
    </div>
  );
}
