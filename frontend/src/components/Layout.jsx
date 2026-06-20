import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  LayoutGrid,
  ListChecks,
  Moon,
  ScanLine,
  ShieldCheck,
  Sun,
} from "lucide-react";
import { getHealth } from "../api.js";
import { toggleTheme, useTheme } from "../hooks/useTheme.js";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutGrid, end: true },
  { to: "/analyze", label: "Analyze", icon: ScanLine },
  { to: "/violations", label: "Records", icon: ListChecks },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

const TODAY = new Date().toLocaleDateString("en-IN", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

export default function Layout() {
  const [online, setOnline] = useState(null);
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const theme = useTheme();

  useEffect(() => {
    const ping = () =>
      getHealth().then(() => setOnline(true)).catch(() => setOnline(false));
    ping();
    const id = setInterval(ping, 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">
            <ShieldCheck size={20} strokeWidth={2} />
          </span>
          <div>
            <strong>TrafficGuard</strong>
            <span className="brand-sub">AI Enforcement</span>
          </div>
        </div>

        <nav>
          <p className="nav-heading">Workspace</p>
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className="nav-link">
              <Icon size={18} strokeWidth={1.75} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-foot">
          <span className={`status-dot ${statusClass(online)}`} />
          {online === null ? "Connecting…" : online ? "Backend online" : "Backend offline"}
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <span className="topbar-date">{TODAY}</span>
          <div className="topbar-actions">
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              title={theme === "dark" ? "Switch to light" : "Switch to dark"}
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun size={17} strokeWidth={1.9} /> : <Moon size={17} strokeWidth={1.9} />}
            </button>
            {pathname !== "/analyze" && (
              <button className="btn-primary" onClick={() => navigate("/analyze")}>
                <ScanLine size={16} strokeWidth={2} />
                New analysis
              </button>
            )}
          </div>
        </header>
        <div className="page rise" key={pathname}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}

const statusClass = (online) =>
  online === null ? "is-idle" : online ? "is-on" : "is-off";
