import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const api = axios.create({ baseURL });

export const uploadImage = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/upload", form).then((r) => r.data);
};

export const getViolations = (params) =>
  api.get("/violations", { params }).then((r) => r.data);

export const getSummary = () =>
  api.get("/analytics/summary").then((r) => r.data);

export const getByType = () =>
  api.get("/analytics/by-type").then((r) => r.data);
