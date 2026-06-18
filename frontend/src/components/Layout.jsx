import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, LayoutGrid, ScanLine, ListChecks } from "lucide-react";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutGrid, end: true },
  { to: "/analyze", label: "Analyze", icon: ScanLine },
  { to: "/violations", label: "Records", icon: ListChecks },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

export default function Layout() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">TG</span>
          <div>
            <strong>TrafficGuard</strong>
            <span className="brand-sub">AI Enforcement</span>
          </div>
        </div>
        <nav>
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className="nav-link">
              <Icon size={18} strokeWidth={1.75} />
              {label}
            </NavLink>
          ))}
        </nav>
        <footer className="sidebar-foot">Gridlock 2.0 · Round 2</footer>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
