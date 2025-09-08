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
          data-oid="u:xxuei"
        >
          <AlertTriangle
            className="h-12 w-12 text-destructive mb-4"
            data-oid="mux5pno"
          />
          <h2 className="text-xl font-semibold mb-2" data-oid=".k78a6y">
            Something went wrong
          </h2>
          <p className="text-muted-foreground mb-6 max-w-md" data-oid="n6:kbnd">
            An unexpected error occurred. Please try refreshing the page or
            contact support if the problem persists.
          </p>
          <div className="flex gap-2" data-oid=":glc51x">
            <Button
              onClick={this.handleReset}
              variant="outline"
              data-oid="9eatqd9"
            >
              <RotateCcw className="h-4 w-4 mr-2" data-oid="z4y1y3h" />
              Try Again
            </Button>
            <Button onClick={() => window.location.reload()} data-oid="fho91o6">
              Refresh Page
            </Button>
          </div>
          {process.env.NODE_ENV === "development" && this.state.error && (
            <details className="mt-6 w-full max-w-2xl" data-oid="wi5dc9p">
              <summary
                className="cursor-pointer text-sm text-muted-foreground"
                data-oid="km_xog5"
              >
                Error Details (Development Only)
              </summary>
              <pre
                className="mt-2 p-4 bg-muted rounded text-left text-xs overflow-auto"
                data-oid="m.vmqu3"
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
