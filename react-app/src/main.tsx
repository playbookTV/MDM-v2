import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { initSentry, ErrorBoundary } from "./lib/sentry";
import App from "./App";
import "./index.css";

// Initialize Sentry
initSentry();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      cacheTime: 5 * 60 * 1000, // 5 minutes
      retry: (failureCount, error) => {
        // Don't retry 4xx errors
        if (error instanceof Error && error.message.includes("4")) {
          return false;
        }
        return failureCount < 3;
      },
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode data-oid="6inq6i9">
    <ErrorBoundary 
      fallback={({ error, resetError }) => (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md mx-auto text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Something went wrong</h2>
            <p className="text-gray-600 mb-6">
              We've encountered an unexpected error. Our team has been notified.
            </p>
            <button
              onClick={resetError}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Try again
            </button>
          </div>
        </div>
      )}
      showDialog
    >
      <QueryClientProvider client={queryClient} data-oid=".f9jelr">
        <BrowserRouter data-oid="y5wrn29">
          <App data-oid="xv8t0u7" />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);
