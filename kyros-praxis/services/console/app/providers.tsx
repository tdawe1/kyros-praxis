'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { SessionProvider } from 'next-auth/react';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { Theme } from '@carbon/react';
import SessionMonitor from '@/components/auth/SessionMonitor';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: any) => {
        if (error.status === 404 || error.status === 401) return false;
        return failureCount < 3;
      },
      // @ts-ignore
      onError: (error: any) => {
        if (error.status === 401) {
          toast.error('Authentication required. Please log in again.');
        } else {
          toast.error(`Query error: ${error.message}`);
        }
      },
    },
    mutations: {
      retry: false,
      // @ts-ignore
      onError: (error: any) => {
        if (error.status === 401) {
          toast.error('Authentication required. Please log in again.');
        } else if (error.status === 403) {
          toast.error('Access denied. Insufficient permissions.');
        } else {
          toast.error(`Mutation error: ${error.message}`);
        }
      },
    },
  },
});

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        <SessionMonitor>
          <Theme theme="g10">{children}</Theme>
          <ReactQueryDevtools initialIsOpen={false} />
          <Toaster position="top-right" />
        </SessionMonitor>
      </QueryClientProvider>
    </SessionProvider>
  );
}
