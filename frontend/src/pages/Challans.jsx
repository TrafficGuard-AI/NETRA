import { useEffect, useMemo, useState } from "react";
import { FileWarning, ImageOff, FolderTree, BadgeCheck } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { challanUrl, getChallanList, getChallanTree, issueChallan } from "../api.js";

const SEVERITY_CLASS = { HIGH: "badge danger", MEDIUM: "badge warning", LOW: "badge" };
const STATUS_CLASS = { issued: "tag ok", pending: "tag pending" };
const pretty = (t) => (t || "").replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
const prettyClass = (c) => ({ two_wheeler: "Two-wheeler", four_wheeler: "Four-wheeler" }[c] || c);

export default function Challans() {
  const [tree, setTree] = useState(null); // { available, tree, total }
  const [rows, setRows] = useState([]);
  const [vclass, setVclass] = useState("");
  const [vtype, setVtype] = useState("");

  useEffect(() => {
    getChallanTree()
      .then(setTree)
      .catch(() => setTree({ available: false, tree: {}, total: 0 }));
  }, []);

  useEffect(() => {
    if (!tree?.available) return;
    getChallanList({
      vehicle_class: vclass || undefined,
      violation_type: vtype || undefined,
      limit: 100,
    })
      .then(setRows)
      .catch(() => setRows([]));
  }, [tree, vclass, vtype]);

  const issue = async (id) => {
    const updated = await issueChallan(id);
    setRows((rs) => rs.map((r) => (r._id === id ? updated : r)));
  };

  // Sub-folder (violation type) options for the currently selected class.
  const typeOptions = useMemo(() => {
    if (!tree?.tree) return [];
    const set = new Set();
    Object.entries(tree.tree).forEach(([c, types]) => {
      if (!vclass || c === vclass) Object.keys(types).forEach((t) => set.add(t));
    });
    return [...set].sort();
  }, [tree, vclass]);

  if (tree && !tree.available) {
    return (
      <section>
        <PageHeader
          eyebrow="Challans"
          title="Challan evidence store"
          lede="Issued challans, filed by vehicle class and violation type."
        />
        <div className="card">
          <EmptyState
            icon={FileWarning}
            title="Challan store offline"
            hint="MongoDB is unreachable. On a cloud host, allow the server's IP in Atlas → Network Access (0.0.0.0/0), then redeploy."
          />
        </div>
      </section>
    );
  }

  const classes = tree ? Object.keys(tree.tree) : [];

  return (
    <section>
      <PageHeader
        eyebrow="Challans"
        title="Challan evidence store"
        lede="Every offending vehicle, filed by class and violation type — ready to issue."
      />

      {/* Folder-tree summary cards */}
      <div className="challan-tree">
        {classes.map((c) => (
          <div key={c} className="card challan-folder">
            <div className="challan-folder-head">
              <FolderTree size={16} strokeWidth={1.8} />
              <span>{prettyClass(c)}</span>
              <span className="count-pill">
                {Object.values(tree.tree[c]).reduce((a, b) => a + b, 0)}
              </span>
            </div>
            <ul className="challan-subfolders">
              {Object.entries(tree.tree[c]).map(([t, n]) => (
                <li key={t}>
                  <span>{pretty(t)}</span>
                  <b className="mono">{n}</b>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="toolbar">
        <select
          value={vclass}
          onChange={(e) => {
            setVclass(e.target.value);
            setVtype("");
          }}
        >
          <option value="">All vehicle classes</option>
          {classes.map((c) => (
            <option key={c} value={c}>
              {prettyClass(c)}
            </option>
          ))}
        </select>
        <select value={vtype} onChange={(e) => setVtype(e.target.value)}>
          <option value="">All violation types</option>
          {typeOptions.map((t) => (
            <option key={t} value={t}>
              {pretty(t)}
            </option>
          ))}
        </select>
        <span className="count-pill">{rows.length} challans</span>
      </div>

      {/* Table */}
      <div className="table-wrap card">
        <table className="table">
          <thead>
            <tr>
              <th aria-label="Evidence"></th>
              <th>Type</th>
              <th>Severity</th>
              <th>Class</th>
              <th>Vehicle</th>
              <th>Plate</th>
              <th>Location</th>
              <th>Confidence</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c._id}>
                <td>
                  <Thumb url={c.evidence_url} />
                </td>
                <td className="strong">{pretty(c.violation_type)}</td>
                <td>
                  <span className={SEVERITY_CLASS[c.severity] || "badge"}>{c.severity}</span>
                </td>
                <td className="faint">{prettyClass(c.vehicle_class)}</td>
                <td>{c.vehicle_type}</td>
                <td className="mono">{c.license_plate || "—"}</td>
                <td className="faint">{c.location || "—"}</td>
                <td>{c.confidence != null ? `${Math.round(c.confidence * 100)}%` : "—"}</td>
                <td>
                  <span className={STATUS_CLASS[c.status] || "tag muted"}>{c.status}</span>
                </td>
                <td>
                  {c.status !== "issued" && (
                    <button className="btn-soft" onClick={() => issue(c._id)}>
                      <BadgeCheck size={14} strokeWidth={2} /> Issue
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && (
          <EmptyState
            icon={FileWarning}
            title="No challans yet"
            hint="Challans are filed automatically when a violation is detected."
          />
        )}
      </div>
    </section>
  );
}

function Thumb({ url }) {
  const [broken, setBroken] = useState(false);
  const src = challanUrl(url);
  if (!src || broken) {
    return (
      <span className="thumb thumb-empty">
        <ImageOff size={15} strokeWidth={1.7} />
      </span>
    );
  }
  return (
    <span className="thumb">
      <img src={src} alt="" loading="lazy" onError={() => setBroken(true)} />
    </span>
  );
}
