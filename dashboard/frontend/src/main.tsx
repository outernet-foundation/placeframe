import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ViewerPage } from "./viewer/ViewerPage";
import "./index.css";

const isViewer = window.location.pathname === "/viewer";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>{isViewer ? <ViewerPage /> : <App />}</React.StrictMode>,
);
