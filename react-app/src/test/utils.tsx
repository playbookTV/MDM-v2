import React, { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient} data-oid="ouq389q">
      <BrowserRouter data-oid="-:2uftl">{children}</BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from "@testing-library/react";
export { customRender as render };

// Common test data factories
export const createMockDataset = (overrides = {}) => ({
  id: "test-dataset-1",
  name: "Test Dataset",
  description: "A test dataset",
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:00:00Z",
  ...overrides,
});

export const createMockScene = (overrides = {}) => ({
  id: "test-scene-1",
  source: "test-image.jpg",
  dataset_id: "test-dataset-1",
  dataset_name: "Test Dataset",
  width: 1920,
  height: 1080,
  scene_type: "living_room",
  scene_conf: 0.85,
  review_status: "pending",
  objects_count: 5,
  r2_key_original: "test-image.jpg",
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:00:00Z",
  ...overrides,
});

export const createMockJob = (overrides = {}) => ({
  id: "test-job-1",
  dataset_id: "test-dataset-1",
  job_type: "process_dataset",
  status: "pending",
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:00:00Z",
  progress: 0,
  total_items: 100,
  processed_items: 0,
  ...overrides,
});

// Mock fetch response helper
export const mockFetchResponse = (data: any, ok = true, status = 200) => {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(data),
  } as Response);
};

// Mock fetch error helper
export const mockFetchError = (message = "Network error") => {
  return Promise.reject(new Error(message));
};
