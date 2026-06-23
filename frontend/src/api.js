import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const api = axios.create({ baseURL });

export const uploadImage = (file, location) => {
  const form = new FormData();
  form.append("file", file);
  if (location) form.append("location", location);
  return api.post("/upload", form).then((r) => r.data);
};

export const uploadVideo = (file, location) => {
  const form = new FormData();
  form.append("file", file);
  if (location) form.append("location", location);
  return api.post("/video-upload", form).then((r) => r.data);
};

export const getViolations = (params) =>
  api.get("/violations", { params }).then((r) => r.data);

export const updateViolationStatus = (id, status) =>
  api.patch(`/violations/${id}`, { status }).then((r) => r.data);

export const getViolationEvidence = (id) =>
  api.get(`/violations/${id}/evidence`).then((r) => r.data);

export const getSummary = () =>
  api.get("/analytics/summary").then((r) => r.data);

export const getByType = () =>
  api.get("/analytics/by-type").then((r) => r.data);

export const getRules = () =>
  api.get("/rules").then((r) => r.data);

export const getTrends = () =>
  api.get("/analytics/trends").then((r) => r.data);

export const getTopPlates = () =>
  api.get("/analytics/top-plates").then((r) => r.data);

export const API_ORIGIN = baseURL.replace(/\/api\/?$/, "");

// Build a servable evidence URL from a stored annotated-image path (any OS separator).
export const evidenceUrl = (path) =>
  path ? `${API_ORIGIN}/evidence/${String(path).split(/[\\/]/).pop()}` : null;

export const getHealth = () =>
  axios.get(`${API_ORIGIN}/health`).then((r) => r.data);

// ── Challan evidence store (MongoDB) ──────────────────────────────────────
export const getChallanTree = () =>
  api.get("/challans").then((r) => r.data);

export const getChallanList = (params) =>
  api.get("/challans/list", { params }).then((r) => r.data);

export const issueChallan = (id) =>
  api.patch(`/challans/${id}/issue`).then((r) => r.data);

// Challan crops are served from the backend's /challans static mount; the API
// returns an evidence_url like "/challans/two_wheeler/HELMET/uuid.jpg".
export const challanUrl = (url) => (url ? `${API_ORIGIN}${url}` : null);
