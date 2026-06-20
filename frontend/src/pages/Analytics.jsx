import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BarChart3, Trophy } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import Donut, { COLORS } from "../components/Donut.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { getByType, getTopPlates, getTrends } from "../api.js";
import { useTheme } from "../hooks/useTheme.js";

const pretty = (t) => t.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());

const CHART = {
  light: { grid: "#eae5dd", tick: "#5c564e", cursor: "#f7f5f1", accent: "#0f766e" },
  dark: { grid: "#2d2823", tick: "#b3aa9d", cursor: "#25201b", accent: "#19a99a" },
};

export default function Analytics() {
  const [data, setData] = useState([]);
  const [trend, setTrend] = useState([]);
  const [topPlates, setTopPlates] = useState([]);

  useEffect(() => {
    getByType()
      .then((rows) => setData(rows.map((r) => ({ name: pretty(r.type), value: r.count }))))
      .catch(() => setData([]));
    getTrends()
      .then((rows) => setTrend(rows.map((r) => ({ date: r.date.slice(5), count: r.count }))))
      .catch(() => setTrend([]));
    getTopPlates().then(setTopPlates).catch(() => setTopPlates([]));
  }, []);

  const theme = useTheme();
  const c = CHART[theme] || CHART.light;
  const total = data.reduce((s, d) => s + d.value, 0);

  if (!data.length) {
    return (
      <section>
        <PageHeader eyebrow="Analytics" title="Violation distribution" lede="How flagged events break down across categories and severity." />
        <div className="card panel">
          <EmptyState icon={BarChart3} title="No analytics yet" hint="Flagged violations will chart here once you analyze images." />
        </div>
      </section>
    );
  }

  return (
    <section>
      <PageHeader
        eyebrow="Analytics"
        title="Violation distribution"
        lede="How flagged events break down across categories, time and offenders."
      />

      <div className="split">
        <div className="card panel">
          <div className="panel-head"><h2>Share by type</h2></div>
          <div className="mix">
            <Donut data={data} total={total} />
            <ul className="legend">
              {data.map((d, i) => (
                <li key={d.name}>
                  <span className="dot" style={{ background: COLORS[i % COLORS.length] }} />
                  {d.name}
                  <strong>{d.value}</strong>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="card panel">
          <div className="panel-head"><h2>Volume by type</h2></div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -18 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={c.grid} vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: c.tick }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: c.tick }} />
              <Tooltip cursor={{ fill: c.cursor }} contentStyle={{ borderRadius: 10, fontSize: 13 }} />
              <Bar dataKey="value" radius={[7, 7, 0, 0]} maxBarSize={64}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="split" style={{ marginTop: 20 }}>
        <div className="card panel">
          <div className="panel-head"><h2>Trend over time</h2><span className="panel-sub">violations per day</span></div>
          {trend.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={trend} margin={{ top: 8, right: 12, bottom: 8, left: -18 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={c.grid} vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: c.tick }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: c.tick }} />
                <Tooltip contentStyle={{ borderRadius: 10, fontSize: 13 }} />
                <Line type="monotone" dataKey="count" stroke={c.accent} strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState icon={BarChart3} title="No trend data yet" />
          )}
        </div>

        <div className="card panel">
          <div className="panel-head"><h2>Top offenders</h2><span className="panel-sub">by plate</span></div>
          {topPlates.length ? (
            <ol className="offenders">
              {topPlates.map((p, i) => (
                <li key={p.plate}>
                  <span className="rank">{i + 1}</span>
                  <span className="mono">{p.plate}</span>
                  <strong>{p.count}</strong>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState icon={Trophy} title="No repeat offenders yet" hint="Plates seen more than once will rank here." />
          )}
        </div>
      </div>
    </section>
  );
}
