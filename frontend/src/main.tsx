import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./style.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {/* BrowserRouter keeps the page in the address bar (/teams, /teams/5), so Back, reload and links work */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
