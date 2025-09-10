import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { act } from 'react-dom/test-utils';
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

  return {
    ...render(ui),
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

// Test for unauthenticated state
test('redirects to login if unauthenticated', async () => {
  const mockPush = jest.fn();
  renderWithProviders(<Home />, mockUnauthenticatedValue, mockPush);

  await waitFor(() => {
    expect(mockPush).toHaveBeenCalledWith('/auth/login');
  });

  expect(screen.queryByText('Welcome to Kyros Console')).not.toBeInTheDocument();
});

// Test for authenticated state
test('renders dashboard with session and WS connected', () => {
  const mockPush = jest.fn();
  renderWithProviders(<Home />, mockSessionValue, mockPush);

  expect(screen.getByText('Welcome to Kyros Console')).toBeInTheDocument();

  const button = screen.getByRole('button', { name: /Go to Jobs/ });
  fireEvent.click(button);
  expect(mockPush).toHaveBeenCalledWith('/jobs');
});

// Test for error handling
test('handles useWebSocket error gracefully', () => {
  const mockSession = { data: { user: { email: 'test@example.com' } }, status: 'authenticated' as const };
  mockedUseWebSocket.mockImplementation(() => { throw new Error('Connection error'); });

  expect(() => {
    renderWithProviders(<Home />, mockSession);
  }).toThrow('Connection error');
});
