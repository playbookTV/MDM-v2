import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode data-oid="6inq6i9">
    <QueryClientProvider client={queryClient} data-oid=".f9jelr">
      <BrowserRouter data-oid="y5wrn29">
        <App data-oid="xv8t0u7" />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
