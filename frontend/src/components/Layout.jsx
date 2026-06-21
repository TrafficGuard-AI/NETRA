import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  LayoutGrid,
  ListChecks,
  Moon,
  ScanLine,
  Sun,
} from "lucide-react";

// The NETRA "eye" mark from the deck.
function EyeMark() {
  return (
    <svg viewBox="0 0 32 32" width="22" height="22" fill="none" aria-hidden>
      <circle cx="16" cy="16" r="11" stroke="currentColor" strokeWidth="2.4" />
      <circle cx="16" cy="16" r="4.4" fill="currentColor" />
      <path
        d="M5 16H2M30 16h-3M16 5V2M16 30v-3"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}
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
            <EyeMark />
          </span>
          <div>
            <strong>NETRA</strong>
            <span className="brand-sub">Command Center</span>
          </div>
        </div>

        <nav>
          <p className="nav-heading">Monitor</p>
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
