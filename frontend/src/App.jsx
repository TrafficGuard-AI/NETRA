import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Analyze from "./pages/Analyze.jsx";
import Violations from "./pages/Violations.jsx";
import Challans from "./pages/Challans.jsx";
import Analytics from "./pages/Analytics.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/violations" element={<Violations />} />
        <Route path="/challans" element={<Challans />} />
        <Route path="/analytics" element={<Analytics />} />
      </Route>
    </Routes>
  );
}
