import { useRef, useState } from "react";
import { ImageUp, Loader2 } from "lucide-react";
import { uploadImage } from "../api.js";

export default function UploadPanel({ onResult, onPreview, onStart, location }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = async (file) => {
    if (!file) return;
    onPreview?.(URL.createObjectURL(file));
    onStart?.();
    setBusy(true);
    setError(null);
    try {
      onResult(await uploadImage(file, location));
    } catch {
      setError("Upload failed — make sure the backend is running.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className={`dropzone${dragging ? " is-dragging" : ""}${busy ? " is-busy" : ""}`}
      onClick={() => !busy && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <span className="dropzone-icon">
        {busy ? (
          <Loader2 size={26} strokeWidth={1.75} className="spin" />
        ) : (
          <ImageUp size={26} strokeWidth={1.5} />
        )}
      </span>
      <p className="dropzone-title">
        {busy ? "Analyzing frame…" : "Drop a traffic image, or click to browse"}
      </p>
      <span className="dropzone-hint">JPG or PNG · single frame</span>
      {error && <span className="dropzone-error">{error}</span>}
    </div>
  );
}
