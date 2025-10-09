 import { render, screen, waitFor } from "@testing-library/react";
 import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
 import SettingsPage from "../app/settings/page";

 // Mock next-auth/react module
 jest.mock("next-auth/react", () => ({
   useSession: jest.fn(),
 }));

 const mockUseSession = require("next-auth/react").useSession;
 mockUseSession.mockReturnValue({
   data: {
     user: { id: "1", email: "test@example.com", name: "Test User" },
     accessToken: "mock-token",
   },
   status: "authenticated",
   update: jest.fn(),
 });

 describe("SettingsPage", () => {
   const queryClient = new QueryClient({
     defaultOptions: { queries: { retry: false } },
   });

   beforeEach(() => {
     queryClient.clear();
     // Setup default mock for useSession
     mockUseSession.mockReturnValue({
       data: {
         user: { id: "1", email: "test@example.com", name: "Test User" },
         accessToken: "mock-token",
       },
       status: "authenticated",
       update: jest.fn(),
     });
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
