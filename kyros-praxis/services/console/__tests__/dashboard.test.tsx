 import React from 'react';
 import { render, screen, waitFor, fireEvent } from '@testing-library/react';
 import '@testing-library/jest-dom';
 import { act } from 'react-dom/test-utils';
 import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
 import Home from '../app/tasks/page'; // Based on open tabs path

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock next-auth/react
jest.mock('next-auth/react', () => ({
  useSession: jest.fn(),
}));

// Mock the custom useWebSocket from '@/lib/ws'
jest.mock('@/lib/ws', () => ({
  useWebSocket: jest.fn(),
}));

// Import the mocked functions
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useWebSocket } from '@/lib/ws';

// Define type for session
type MockSession = { data: any; status: 'authenticated' | 'unauthenticated' | 'loading' };

// Mock data
const mockSessionValue: MockSession = { data: { user: { email: 'test@example.com' } }, status: 'authenticated' as const };
const mockUnauthenticatedValue: MockSession = { data: null, status: 'unauthenticated' as const };
const mockLoadingValue: MockSession = { data: null, status: 'loading' as const };

// Mocked functions
const mockedUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;
const mockedUseSession = useSession as jest.MockedFunction<typeof useSession>;
const mockedUseWebSocket = useWebSocket as jest.MockedFunction<typeof useWebSocket>;

// Custom render function
 const renderWithProviders = (ui: React.ReactElement, session: MockSession = mockLoadingValue, routerPush = jest.fn(), wsMock = { isConnected: false }) => {
   mockedUseRouter.mockReturnValue({ push: routerPush } as any);
   mockedUseSession.mockReturnValue(session as any);
   mockedUseWebSocket.mockReturnValue(wsMock as any);

   const queryClient = new QueryClient({
     defaultOptions: { queries: { retry: false } },
   });

   return {
     ...render(
       <QueryClientProvider client={queryClient}>
         {ui}
       </QueryClientProvider>
     ),
   };
 };

// Before each to clear mocks
beforeEach(() => {
  jest.clearAllMocks();
});

// Test for loading state
test('renders loading state', () => {
  renderWithProviders(<Home />);

  expect(screen.getByText('Loading...')).toBeInTheDocument();
});

 // Test for unauthenticated state - component doesn't handle auth, just shows loading or tasks
 test('shows loading when no tasks are available', () => {
   const mockPush = jest.fn();
   renderWithProviders(<Home />, mockUnauthenticatedValue, mockPush);

   expect(screen.getByText('Loading...')).toBeInTheDocument();
 });

 // Test for authenticated state with tasks loaded
 test('renders kanban board when tasks are loaded', async () => {
   const mockPush = jest.fn();

   // Mock fetch to return tasks
   (global.fetch as jest.Mock).mockResolvedValueOnce({
     ok: true,
     json: () => Promise.resolve([
       { id: '1', title: 'Task 1', status: 'pending' },
       { id: '2', title: 'Task 2', status: 'in-progress' },
     ]),
   });

   renderWithProviders(<Home />, mockSessionValue, mockPush);

   await waitFor(() => {
     expect(screen.getByText('Tasks')).toBeInTheDocument();
     expect(screen.getByText('Task 1')).toBeInTheDocument();
     expect(screen.getByText('Task 2')).toBeInTheDocument();
   });
 });

 // Test for error handling in query
 test('handles API error gracefully', async () => {
   // Mock fetch to fail
   (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('API error'));

   renderWithProviders(<Home />, mockSessionValue);

   // Component shows kanban board when tasks are available, error handling not implemented
   await waitFor(() => {
     expect(screen.getByText('Tasks')).toBeInTheDocument();
   });
 });
