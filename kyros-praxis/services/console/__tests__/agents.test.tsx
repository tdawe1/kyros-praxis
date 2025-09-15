 import { render, screen, waitFor } from '@testing-library/react';
 import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
 import { server } from '@/mocks/server';
 import AgentsPage from '../app/(dashboard)/agents/page';

 jest.mock('next/navigation', () => ({
   useRouter: () => ({
     push: jest.fn(),
     replace: jest.fn(),
     back: jest.fn(),
     forward: jest.fn(),
     refresh: jest.fn(),
     prefetch: jest.fn(),
   }),
   useSearchParams: () => new URLSearchParams(),
 }));

 jest.mock('../app/hooks/useAgents', () => ({
   useAgents: jest.fn(),
   useBulkUpdateAgents: jest.fn(),
   useBulkDeleteAgents: jest.fn(),
   useRunAgent: jest.fn(),
 }));

 import { useAgents, useBulkUpdateAgents, useBulkDeleteAgents, useRunAgent } from '../app/hooks/useAgents';

 const mockUseAgents = useAgents as jest.MockedFunction<typeof useAgents>;
 const mockUseBulkUpdateAgents = useBulkUpdateAgents as jest.MockedFunction<typeof useBulkUpdateAgents>;
 const mockUseBulkDeleteAgents = useBulkDeleteAgents as jest.MockedFunction<typeof useBulkDeleteAgents>;
 const mockUseRunAgent = useRunAgent as jest.MockedFunction<typeof useRunAgent>;

 const queryClient = new QueryClient({
   defaultOptions: { queries: { retry: false } },
 });

 describe('Agents Page Integration Test', () => {
   const wrapper = ({ children }: { children: React.ReactNode }) => (
     <QueryClientProvider client={queryClient}>
       {children}
     </QueryClientProvider>
   );

   beforeEach(() => {
     mockUseAgents.mockReturnValue({
       data: {
         agents: [
           {
             id: '1',
             name: 'Test Agent 1',
             status: 'active',
             model: 'gpt-4-turbo',
             temperature: 0.7,
             maxTokens: 4096,
             topP: 1,
             frequencyPenalty: 0,
             presencePenalty: 0,
             owner: 'user1',
             capabilities: [],
             policies: [],
             connectors: [],
             tags: [],
             collaborators: [],
             createdAt: new Date(),
             updatedAt: new Date(),
             runCount: 0,
             totalTokensUsed: 0,
             estimatedCost: 0,
             version: '1.0.0',
           } as any,
           {
             id: '2',
             name: 'Test Agent 2',
             status: 'paused',
             model: 'claude-3-opus',
             temperature: 0.7,
             maxTokens: 4096,
             topP: 1,
             frequencyPenalty: 0,
             presencePenalty: 0,
             owner: 'user2',
             capabilities: [],
             policies: [],
             connectors: [],
             tags: [],
             collaborators: [],
             createdAt: new Date(),
             updatedAt: new Date(),
             runCount: 0,
             totalTokensUsed: 0,
             estimatedCost: 0,
             version: '1.0.0',
           } as any,
         ],
         total: 2,
         page: 1,
         pageSize: 20,
       },
       isLoading: false,
       error: null,
       isError: false,
       isPending: false,
       isLoadingError: false,
       isRefetchError: false,
       isSuccess: true,
       status: 'success',
       dataUpdatedAt: Date.now(),
       errorUpdatedAt: 0,
       failureCount: 0,
       failureReason: null,
       errorUpdateCount: 0,
       isFetched: true,
       isFetchedAfterMount: true,
       isFetching: false,
       isRefetching: false,
       refetch: jest.fn(),
       fetchStatus: 'idle',
     } as any);

     mockUseBulkUpdateAgents.mockReturnValue({
       mutate: jest.fn(),
       mutateAsync: jest.fn(),
       reset: jest.fn(),
       isIdle: true,
       isPending: false,
       isSuccess: false,
       isError: false,
       data: undefined,
       error: null,
       variables: undefined,
       submit: jest.fn(),
     } as any);

     mockUseBulkDeleteAgents.mockReturnValue({
       mutate: jest.fn(),
       mutateAsync: jest.fn(),
       reset: jest.fn(),
       isIdle: true,
       isPending: false,
       isSuccess: false,
       isError: false,
       data: undefined,
       error: null,
       variables: undefined,
       submit: jest.fn(),
     } as any);

     mockUseRunAgent.mockReturnValue({
       mutate: jest.fn(),
       mutateAsync: jest.fn(),
       reset: jest.fn(),
       isIdle: true,
       isPending: false,
       isSuccess: false,
       isError: false,
       data: undefined,
       error: null,
       variables: undefined,
       submit: jest.fn(),
     } as any);
   });

   beforeAll(() => server.listen());
   afterEach(() => {
     server.resetHandlers();
     queryClient.clear();
   });
   afterAll(() => server.close());

   it('renders agents data correctly', async () => {
     render(<AgentsPage />, { wrapper });

     // Should render table directly since isLoading is false
     expect(screen.getByText('Test Agent 1')).toBeInTheDocument();
     expect(screen.getByText('Test Agent 2')).toBeInTheDocument();
   });
});