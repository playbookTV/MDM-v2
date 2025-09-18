import * as Sentry from "@sentry/react";
import { useEffect } from "react";
import { useLocation, useNavigationType, createRoutesFromChildren } from "react-router-dom";

export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  
  if (!dsn) {
    console.log("Sentry DSN not configured, skipping initialization");
    return;
  }

  Sentry.init({
    dsn,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
      Sentry.reactRouterV6BrowserTracingIntegration({
        useEffect,
        useLocation,
        useNavigationType,
        createRoutesFromChildren,
      }),
    ],
    tracesSampleRate: import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    environment: import.meta.env.VITE_ENVIRONMENT || "development",
    release: `modomo-web@${import.meta.env.VITE_APP_VERSION || "1.0.0"}`,
    beforeSend(event, hint) {
      // Filter out certain errors
      if (event.exception) {
        const error = hint.originalException;
        
        // Don't send network errors in development
        if (
          import.meta.env.DEV &&
          error instanceof Error &&
          error.message.includes("fetch")
        ) {
          return null;
        }
      }
      
      return event;
    },
    beforeBreadcrumb(breadcrumb) {
      // Filter sensitive data from breadcrumbs
      if (breadcrumb.category === "console") {
        return null; // Don't send console logs
      }
      
      if (breadcrumb.type === "http") {
        // Sanitize auth headers
        if (breadcrumb.data?.request?.headers) {
          const headers = breadcrumb.data.request.headers;
          if (headers.Authorization) {
            headers.Authorization = "[REDACTED]";
          }
        }
      }
      
      return breadcrumb;
    },
  });
}

export const ErrorBoundary = Sentry.ErrorBoundary;
export const withProfiler = Sentry.withProfiler;
export const captureException = Sentry.captureException;
export const captureMessage = Sentry.captureMessage;
export const setUser = Sentry.setUser;
export const setContext = Sentry.setContext;
export const addBreadcrumb = Sentry.addBreadcrumb;