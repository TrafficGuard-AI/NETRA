import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { uploadImage } from "../api.js";

export default function UploadPanel({ onResult }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = async (file) => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      onResult(await uploadImage(file));
    } catch {
      setError("Upload failed — is the backend running?");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className={`dropzone${dragging ? " is-dragging" : ""}`}
      onClick={() => inputRef.current?.click()}
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
      <UploadCloud size={28} strokeWidth={1.5} />
      <p className="dropzone-title">
        {busy ? "Analyzing…" : "Drop a traffic image or click to browse"}
      </p>
      <span className="dropzone-hint">JPG or PNG · single frame</span>
      {error && <span className="dropzone-error">{error}</span>}
    </div>
  );
}
