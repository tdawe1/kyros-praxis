import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { server } from '../src/mocks/server'; // Adjust path as needed
import TasksPage from '../app/tasks/page'; // Adjust path as needed

describe('Tasks Page Integration Test', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  it('renders and fetches tasks data correctly', async () => {
    render(<TasksPage />, { wrapper });

    // Validate loading state (stub for UI validation)
    expect(screen.getByText(/loading/i)).toBeInTheDocument(); // Assume page shows loading text for Kanban board

    // Wait for API integration and data rendering (Kanban layout validation)
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
      expect(screen.getByText('pending')).toBeInTheDocument(); // Basic UI validation for status in Kanban
    });
  });

  it('handles API error gracefully', async () => {
    // Mock error response
    server.use(
      http.get('/collab/state/tasks', () => {
        return new HttpResponse(null, { status: 500 });
      }),
    );

    render(<TasksPage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument(); // Assume page shows error message for Kanban
    });
  });
});