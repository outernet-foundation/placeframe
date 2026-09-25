import { useState } from "react";
import "./App.css";
import { CapturesPage } from "./CapturesPage";
import { MapsPage } from "./MapsPage";

type Tab = "captures" | "maps";

export default function App() {
  const [tab, setTab] = useState<Tab>("captures");
  return (
    <div className="app">
      <header className="app-header">
        <h1>Placeframe Dashboard</h1>
        <nav className="tabs">
          <button className={tab === "captures" ? "tab tab-active" : "tab"} onClick={() => setTab("captures")}>
            Captures
          </button>
          <button className={tab === "maps" ? "tab tab-active" : "tab"} onClick={() => setTab("maps")}>
            Maps
          </button>
        </nav>
      </header>
      {/* The captures tree stays mounted because it holds expansion, selection and in-flight job
          polling that a remount would drop. The map list is mounted on demand instead: it holds
          nothing worth keeping, and mounting fetches it, so it is never stale after a publish. */}
      <main>
        <div hidden={tab !== "captures"}>
          <CapturesPage />
        </div>
        {tab === "maps" ? <MapsPage /> : null}
      </main>
    </div>
  );
}
