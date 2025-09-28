'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { SessionProvider } from 'next-auth/react';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { Theme } from '@carbon/react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: any) => {
        if (error.status === 404 || error.status === 401) return false;
        return failureCount < 3;
      },
      // @ts-ignore
      onError: (error: any) => {
        toast.error(`Query error: ${error.message}`);
      },
    },
    mutations: {
      retry: false,
      // @ts-ignore
      onError: (error: any) => {
        toast.error(`Mutation error: ${error.message}`);
      },
    },
  },
});

interface ProvidersProps {
  children: React.ReactNode;
  nonce?: string;
}

export default function Providers({ children, nonce }: ProvidersProps) {
  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        <Theme theme="g10">{children}</Theme>
        <ReactQueryDevtools initialIsOpen={false} />
        <Toaster position="top-right" />
      </QueryClientProvider>
    </SessionProvider>
  );
}
