import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import AgentsPage from '../page';
import { useAgents, useBulkUpdateAgents, useBulkDeleteAgents, useRunAgent } from '../../../hooks/useAgents';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Mock hooks
jest.mock('../../../hooks/useAgents', () => ({
  useAgents: jest.fn(),
  useBulkUpdateAgents: jest.fn(),
  useBulkDeleteAgents: jest.fn(),
  useRunAgent: jest.fn(),
}));

// Mock Carbon components that might have issues in tests
jest.mock('@carbon/react', () => ({
  ...jest.requireActual('@carbon/react'),
  DataTableSkeleton: () => <div data-testid="skeleton">Loading...</div>,
}));

const mockAgentsData = {
  agents: [
    {
      id: '1',
      name: 'Test Agent 1',
      description: 'Test description',
      status: 'active',
      model: 'gpt-4-turbo',
      owner: 'user@example.com',
      capabilities: ['cap1', 'cap2'],
      tags: ['test', 'demo'],
      lastRunAt: new Date('2024-03-10T14:30:00'),
      successRate: 95.5,
    },
    {
      id: '2',
      name: 'Test Agent 2',
      description: 'Another test',
      status: 'paused',
      model: 'claude-3-opus',
      owner: 'admin@example.com',
      capabilities: [],
      tags: ['production'],
      lastRunAt: null,
      successRate: null,
    },
  ],
  total: 2,
  page: 1,
  pageSize: 20,
};

describe('AgentsPage', () => {
  let queryClient: QueryClient;
  const mockPush = jest.fn();
  const mockSearchParams = new URLSearchParams();

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });

    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);

    (useBulkUpdateAgents as jest.Mock).mockReturnValue({
      mutate: jest.fn(),
    });

    (useBulkDeleteAgents as jest.Mock).mockReturnValue({
      mutate: jest.fn(),
    });

    (useRunAgent as jest.Mock).mockReturnValue({
      mutate: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const renderWithClient = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  it('should display loading state initially', () => {
    (useAgents as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    renderWithClient(<AgentsPage />);
    
    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
  });

  it('should display error state when fetch fails', () => {
    (useAgents as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: { message: 'Failed to fetch agents' },
    });

    renderWithClient(<AgentsPage />);
    
    expect(screen.getByText(/Error loading agents/i)).toBeInTheDocument();
    expect(screen.getByText(/Failed to fetch agents/i)).toBeInTheDocument();
  });

  it('should display empty state when no agents exist', () => {
    (useAgents as jest.Mock).mockReturnValue({
      data: { agents: [], total: 0 },
      isLoading: false,
      error: null,
    });

    renderWithClient(<AgentsPage />);
    
    expect(screen.getByText(/No agents yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Create your first AI agent/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Create Agent/i })).toHaveAttribute('href', '/agents/new');
  });

  it('should display agents table with data', () => {
    (useAgents as jest.Mock).mockReturnValue({
      data: mockAgentsData,
      isLoading: false,
      error: null,
    });

    renderWithClient(<AgentsPage />);
    
    expect(screen.getByText('Test Agent 1')).toBeInTheDocument();
    expect(screen.getByText('Test Agent 2')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
  });

  it('should handle search input', async () => {
    (useAgents as jest.Mock).mockReturnValue({
      data: mockAgentsData,
      isLoading: false,
      error: null,
    });

    renderWithClient(<AgentsPage />);
    
    const searchInput = screen.getByPlaceholderText(/Search agents/i);
    fireEvent.change(searchInput, { target: { value: 'test search' } });
    
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(expect.stringContaining('search=test+search'));
    });
  });

  it('should handle bulk pause action', async () => {
    const mockBulkUpdate = jest.fn();
    (useBulkUpdateAgents as jest.Mock).mockReturnValue({
      mutate: mockBulkUpdate,
    });

    (useAgents as jest.Mock).mockReturnValue({
      data: mockAgentsData,
      isLoading: false,
      error: null,
    });

    renderWithClient(<AgentsPage />);
    
    // Select agents
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]); // Select first agent
    
    // Click pause action
    const pauseButton = screen.getByText(/Pause/i);
    fireEvent.click(pauseButton);
    
    expect(mockBulkUpdate).toHaveBeenCalledWith({
      ids: expect.any(Array),
      update: { status: 'paused' },
    });
  });

  it('should handle pagination', async () => {
    (useAgents as jest.Mock).mockReturnValue({
      data: { ...mockAgentsData, total: 100 },
      isLoading: false,
      error: null,
    });

    renderWithClient(<AgentsPage />);
    
    const nextButton = screen.getByText(/Next page/i);
    fireEvent.click(nextButton);
    
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(expect.stringContaining('page=2'));
    });
  });

  it('should display correct status tags', () => {
    (useAgents as jest.Mock).mockReturnValue({
      data: mockAgentsData,
      isLoading: false,
      error: null,
    });

    renderWithClient(<AgentsPage />);
    
    const activeTag = screen.getByText('Active');
    const pausedTag = screen.getByText('Paused');
    
    expect(activeTag).toHaveClass('cds--tag--green');
    expect(pausedTag).toHaveClass('cds--tag--gray');
  });

  it('should handle delete confirmation modal', async () => {
    const mockBulkDelete = jest.fn();
    (useBulkDeleteAgents as jest.Mock).mockReturnValue({
      mutate: mockBulkDelete,
    });

    (useAgents as jest.Mock).mockReturnValue({
      data: mockAgentsData,
      isLoading: false,
      error: null,
    });

    renderWithClient(<AgentsPage />);
    
    // Select an agent
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]);
    
    // Click delete action
    const deleteButton = screen.getByText(/Delete/i);
    fireEvent.click(deleteButton);
    
    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /Delete/i });
    fireEvent.click(confirmButton);
    
    expect(mockBulkDelete).toHaveBeenCalled();
  });

  it('should navigate to agent detail on row click', () => {
    (useAgents as jest.Mock).mockReturnValue({
      data: mockAgentsData,
      isLoading: false,
      error: null,
    });

    renderWithClient(<AgentsPage />);
    
    const agentLink = screen.getByText('Test Agent 1');
    expect(agentLink.closest('a')).toHaveAttribute('href', '/agents/1');
  });
});