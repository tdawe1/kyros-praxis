import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth";
import SettingsPage from "../app/settings/page";

jest.mock("@tanstack/react-query");
jest.mock("@/lib/auth");

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
mockUseAuth.mockReturnValue({ token: "mock-token" });

const mockQueryClient = new QueryClient();

describe("SettingsPage", () => {
  it("renders loading state", () => {
    const { container } = render(
      <QueryClientProvider client={mockQueryClient}>
        <SettingsPage />
      </QueryClientProvider>
    );
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  it("renders error state", () => {
    const { container } = render(
      <QueryClientProvider client={mockQueryClient}>
        <SettingsPage />
      </QueryClientProvider>
    );
    expect(screen.getByTestId("error")).toBeInTheDocument();
  });

  it("renders settings content", () => {
    const { container } = render(
      <QueryClientProvider client={mockQueryClient}>
        <SettingsPage />
      </QueryClientProvider>
    );
    expect(screen.getByTestId("settings-content")).toBeInTheDocument();
    expect(screen.getByTestId("save-settings")).toBeInTheDocument();
  });
});
