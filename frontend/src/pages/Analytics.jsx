import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getByType } from "../api.js";

const BARS = ["#0f766e", "#b4452f", "#9a6b1f", "#3f6f8f"];

export default function Analytics() {
  const [data, setData] = useState([]);

  useEffect(() => {
    getByType()
      .then((rows) => setData(rows.map((r) => ({ name: r.type.replace(/_/g, " "), count: r.count }))))
      .catch(() => setData([]));
  }, []);

  return (
    <section>
      <header className="page-head">
        <p className="eyebrow">Analytics</p>
        <h1>Violation distribution</h1>
        <p className="lede">How flagged events break down by category.</p>
      </header>

      <div className="card chart-card">
        {data.length ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ece9e3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#6b6660" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#6b6660" }} />
              <Tooltip cursor={{ fill: "#faf9f7" }} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {data.map((_, i) => (
                  <Cell key={i} fill={BARS[i % BARS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="empty">No data yet.</p>
        )}
      </div>
    </section>
  );
}
