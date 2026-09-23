import "./App.css";
import { CapturesPage } from "./CapturesPage";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Placeframe Dashboard</h1>
      </header>
      <main>
        <CapturesPage />
      </main>
    </div>
  );
}
