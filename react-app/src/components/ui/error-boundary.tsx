import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "./button";
import { logError } from "@/lib/error-handling";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logError(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: true,
    });

    this.props.onError?.(error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center"
          data-oid="_xjcbu5"
        >
          <AlertTriangle
            className="h-12 w-12 text-destructive mb-4"
            data-oid="75dxlup"
          />

          <h2 className="text-xl font-semibold mb-2" data-oid="96qhuyt">
            Something went wrong
          </h2>
          <p className="text-muted-foreground mb-6 max-w-md" data-oid="5z1l0nj">
            An unexpected error occurred. Please try refreshing the page or
            contact support if the problem persists.
          </p>
          <div className="flex gap-2" data-oid="471rhv3">
            <Button
              onClick={this.handleReset}
              variant="outline"
              data-oid="p:x7m1m"
            >
              <RotateCcw className="h-4 w-4 mr-2" data-oid="2eiiw8h" />
              Try Again
            </Button>
            <Button onClick={() => window.location.reload()} data-oid="rv0n_ay">
              Refresh Page
            </Button>
          </div>
          {process.env.NODE_ENV === "development" && this.state.error && (
            <details className="mt-6 w-full max-w-2xl" data-oid="d3l.ltd">
              <summary
                className="cursor-pointer text-sm text-muted-foreground"
                data-oid="05ggep2"
              >
                Error Details (Development Only)
              </summary>
              <pre
                className="mt-2 p-4 bg-muted rounded text-left text-xs overflow-auto"
                data-oid="ar-07ht"
              >
                {this.state.error.stack}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
