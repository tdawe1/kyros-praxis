 import { render, screen, waitFor } from "@testing-library/react";
 import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
 import { useAuth } from "@/lib/auth";
 import SettingsPage from "../app/settings/page";

 jest.mock("@/lib/auth");

 const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
 mockUseAuth.mockReturnValue({
   user: { id: "1", email: "test@example.com", name: "Test User" },
   token: "mock-token",
   login: jest.fn(),
   logout: jest.fn(),
 });

 describe("SettingsPage", () => {
   const queryClient = new QueryClient({
     defaultOptions: { queries: { retry: false } },
   });

   beforeEach(() => {
     queryClient.clear();
   });

   it("renders loading state", () => {
     render(
       <QueryClientProvider client={queryClient}>
         <SettingsPage />
       </QueryClientProvider>
     );
     expect(screen.getByTestId("loading")).toBeInTheDocument();
   });

   it("renders error state", async () => {
     // Mock fetch to throw error
     global.fetch = jest.fn(() =>
       Promise.reject(new Error("Network error"))
     ) as jest.Mock;

     render(
       <QueryClientProvider client={queryClient}>
         <SettingsPage />
       </QueryClientProvider>
     );

     await waitFor(() => {
       expect(screen.getByTestId("error")).toBeInTheDocument();
     });
   });

   it("renders settings content", async () => {
     // Mock fetch to return data
     global.fetch = jest.fn(() =>
       Promise.resolve({
         ok: true,
         json: () => Promise.resolve({ theme: "dark" }),
       })
     ) as jest.Mock;

     render(
       <QueryClientProvider client={queryClient}>
         <SettingsPage />
       </QueryClientProvider>
     );

     await waitFor(() => {
       expect(screen.getByTestId("settings-content")).toBeInTheDocument();
       expect(screen.getByTestId("save-settings")).toBeInTheDocument();
     });
   });
 });
