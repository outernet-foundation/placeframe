import { useState } from "react";
import "./App.css";
import { LocalizeTab } from "./tabs/LocalizeTab";
import { ReconstructTab } from "./tabs/ReconstructTab";
import { ToolsTab } from "./tabs/ToolsTab";
import { VisualizeTab } from "./tabs/VisualizeTab";

type Tab = "reconstruct" | "visualize" | "localize" | "tools";

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
          <button className={tab === "localize" ? "active" : ""} onClick={() => setTab("localize")}>
            Localize
          </button>
          <button className={tab === "visualize" ? "active" : ""} onClick={() => setTab("visualize")}>
            Visualize
          </button>
          <button className={tab === "tools" ? "active" : ""} onClick={() => setTab("tools")}>
            Tools
          </button>
        </nav>
      </header>
      <main>
        {tab === "reconstruct" && <ReconstructTab />}
        {tab === "visualize" && <VisualizeTab />}
        {tab === "localize" && <LocalizeTab />}
        {tab === "tools" && <ToolsTab />}
      </main>
    </div>
  );
}
