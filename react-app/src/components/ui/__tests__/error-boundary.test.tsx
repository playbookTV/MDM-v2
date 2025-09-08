import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@/test/utils";
import ErrorBoundary from "../error-boundary";

// Mock logError function
vi.mock("@/lib/error-handling", () => ({
  logError: vi.fn(),
}));

const mockLogError = vi.mocked(await import("@/lib/error-handling")).logError;

// Component that throws an error
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error("Test error");
  }
  return <div data-oid="g58yrar">No error</div>;
};

describe("ErrorBoundary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Suppress console.error for these tests
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("should render children when there is no error", () => {
    render(
      <ErrorBoundary data-oid="y-xdhs1">
        <ThrowError data-oid="bslmoq:" />
      </ErrorBoundary>,
    );

    expect(screen.getByText("No error")).toBeInTheDocument();
  });

  it("should render error UI when child throws error", () => {
    render(
      <ErrorBoundary data-oid="aeofgp-">
        <ThrowError shouldThrow data-oid=".k2l2lx" />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(
      screen.getByText(/An unexpected error occurred/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /try again/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /refresh page/i }),
    ).toBeInTheDocument();
  });

  it("should log error when child throws", () => {
    render(
      <ErrorBoundary data-oid="bj4p6an">
        <ThrowError shouldThrow data-oid=":bm_4z9" />
      </ErrorBoundary>,
    );

    expect(mockLogError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String),
        errorBoundary: true,
      }),
    );
  });

  it("should call onError callback when provided", () => {
    const onError = vi.fn();

    render(
      <ErrorBoundary onError={onError} data-oid="tppi383">
        <ThrowError shouldThrow data-oid="mh8q_e4" />
      </ErrorBoundary>,
    );

    expect(onError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String),
      }),
    );
  });

  it("should render custom fallback when provided", () => {
    const fallback = <div data-oid=".k.hbtr">Custom error message</div>;

    render(
      <ErrorBoundary fallback={fallback} data-oid="kj_9f.d">
        <ThrowError shouldThrow data-oid="kd9450." />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Custom error message")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("should reset error state when try again is clicked", () => {
    const { rerender } = render(
      <ErrorBoundary data-oid=".dj41bz">
        <ThrowError shouldThrow data-oid="la-o2rk" />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    // Click try again
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));

    // Re-render with non-throwing component
    rerender(
      <ErrorBoundary data-oid="_ft36uk">
        <ThrowError shouldThrow={false} data-oid=":rxgq36" />
      </ErrorBoundary>,
    );

    expect(screen.getByText("No error")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("should show error details in development mode", () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = "development";

    render(
      <ErrorBoundary data-oid="tbndb-:">
        <ThrowError shouldThrow data-oid="ga28atg" />
      </ErrorBoundary>,
    );

    expect(
      screen.getByText("Error Details (Development Only)"),
    ).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it("should not show error details in production mode", () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = "production";

    render(
      <ErrorBoundary data-oid="ms179gb">
        <ThrowError shouldThrow data-oid=".sdvcsw" />
      </ErrorBoundary>,
    );

    expect(
      screen.queryByText("Error Details (Development Only)"),
    ).not.toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it("should refresh page when refresh button is clicked", () => {
    // Mock window.location.reload
    const mockReload = vi.fn();
    Object.defineProperty(window.location, "reload", {
      value: mockReload,
      writable: true,
    });

    render(
      <ErrorBoundary data-oid="o-bk13:">
        <ThrowError shouldThrow data-oid="pvczw1-" />
      </ErrorBoundary>,
    );

    fireEvent.click(screen.getByRole("button", { name: /refresh page/i }));

    expect(mockReload).toHaveBeenCalled();
  });
});
