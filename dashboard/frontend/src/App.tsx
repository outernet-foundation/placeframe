import "./App.css";
import { CapturesPage } from "./CapturesPage";

// One page: the captures tree. Publishing state lives on it too (a published map's
// reconstruction is filled green, its capture outlined), so a separate Maps list would only
// repeat it.
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
