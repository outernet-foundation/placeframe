import { useState } from "react";
import "./App.css";
import { ReconstructTab } from "./tabs/ReconstructTab";
import { VisualizeTab } from "./tabs/VisualizeTab";

type Tab = "reconstruct" | "visualize";

export default function App() {
  const [tab, setTab] = useState<Tab>("reconstruct");

  return (
    <div className="app">
      <header className="app-header">
        <h1>Placeframe Dashboard</h1>
        <nav className="tabs">
          <button className={tab === "reconstruct" ? "active" : ""} onClick={() => setTab("reconstruct")}>
            Reconstruct
          </button>
          <button className={tab === "visualize" ? "active" : ""} onClick={() => setTab("visualize")}>
            Visualize
          </button>
        </nav>
      </header>
      <main>{tab === "reconstruct" ? <ReconstructTab /> : <VisualizeTab />}</main>
    </div>
  );
}
