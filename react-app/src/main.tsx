import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode data-oid="dy0-96.">
    <QueryClientProvider client={queryClient} data-oid="5sr03-0">
      <BrowserRouter data-oid="wbkaxgl">
        <App data-oid="coa2wd6" />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
