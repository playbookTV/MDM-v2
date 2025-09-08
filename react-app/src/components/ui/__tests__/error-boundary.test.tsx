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
  return <div data-oid="c23--55">No error</div>;
};

describe("ErrorBoundary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Suppress console.error for these tests
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("should render children when there is no error", () => {
    render(
      <ErrorBoundary data-oid="qo:u_vd">
        <ThrowError data-oid="ryaw1i-" />
      </ErrorBoundary>,
    );

    expect(screen.getByText("No error")).toBeInTheDocument();
  });

  it("should render error UI when child throws error", () => {
    render(
      <ErrorBoundary data-oid="1f-le0g">
        <ThrowError shouldThrow data-oid="076vmvf" />
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
      <ErrorBoundary data-oid="4sz2t4k">
        <ThrowError shouldThrow data-oid="d0:ddp:" />
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
      <ErrorBoundary onError={onError} data-oid=".0v-617">
        <ThrowError shouldThrow data-oid="wd6e3vr" />
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
    const fallback = <div data-oid="uig9.s-">Custom error message</div>;

    render(
      <ErrorBoundary fallback={fallback} data-oid="._4a8k1">
        <ThrowError shouldThrow data-oid="6a017tx" />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Custom error message")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("should reset error state when try again is clicked", () => {
    const { rerender } = render(
      <ErrorBoundary data-oid="50lb5s1">
        <ThrowError shouldThrow data-oid=".hipgfj" />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    // Click try again
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));

    // Re-render with non-throwing component
    rerender(
      <ErrorBoundary data-oid="wb3hlfj">
        <ThrowError shouldThrow={false} data-oid="4aa8r1p" />
      </ErrorBoundary>,
    );

    expect(screen.getByText("No error")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("should show error details in development mode", () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = "development";

    render(
      <ErrorBoundary data-oid="yzkgsg.">
        <ThrowError shouldThrow data-oid="zzddoxb" />
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
      <ErrorBoundary data-oid="icaxv0t">
        <ThrowError shouldThrow data-oid="9f.wmdi" />
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
      <ErrorBoundary data-oid="6hp6_04">
        <ThrowError shouldThrow data-oid="fhxh5f6" />
      </ErrorBoundary>,
    );

    fireEvent.click(screen.getByRole("button", { name: /refresh page/i }));

    expect(mockReload).toHaveBeenCalled();
  });
});
