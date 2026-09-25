import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ViewerPage } from "./viewer/ViewerPage";
import { AlignPage } from "./align/AlignPage";
import "./index.css";

const path = window.location.pathname;
const isViewer = path === "/viewer";
const isAlign = path === "/align";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>{isViewer ? <ViewerPage /> : isAlign ? <AlignPage /> : <App />}</React.StrictMode>,
);
