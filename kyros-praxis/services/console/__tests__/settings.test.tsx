import { render, screen } from "@testing-library/react";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import SettingsPage from "../app/settings/page";

jest.mock("@tanstack/react-query", () => {
  const actual = jest.requireActual("@tanstack/react-query");
  return { ...actual, useQuery: jest.fn() };
});

jest.mock("@/lib/auth", () => ({
  useAuth: () => ({
    user: null,
    token: "mock-token",
    login: jest.fn(),
    logout: jest.fn(),
  }),
}));

const mockQueryClient = new QueryClient();
const mockedUseQuery = useQuery as jest.MockedFunction<typeof useQuery>;

describe("SettingsPage", () => {
  beforeEach(() => {
    mockedUseQuery.mockReset();
  });

  it("renders loading state", () => {
    mockedUseQuery.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    } as any);
    const { container } = render(
      <QueryClientProvider client={mockQueryClient}>
        <SettingsPage />
      </QueryClientProvider>
    );
    expect(screen.getByTestId("loading")).toBeInTheDocument();
  });

  it("renders error state", () => {
    mockedUseQuery.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("boom"),
    } as any);
    const { container } = render(
      <QueryClientProvider client={mockQueryClient}>
        <SettingsPage />
      </QueryClientProvider>
    );
    expect(screen.getByTestId("error")).toBeInTheDocument();
  });

  it("renders settings content", () => {
    mockedUseQuery.mockReturnValue({
      data: { theme: "dark" },
      isLoading: false,
      error: null,
    } as any);
    const { container } = render(
      <QueryClientProvider client={mockQueryClient}>
        <SettingsPage />
      </QueryClientProvider>
    );
    expect(screen.getByTestId("settings-content")).toBeInTheDocument();
    expect(screen.getByTestId("save-settings")).toBeInTheDocument();
  });
});
