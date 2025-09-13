'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { ReactNode, useState } from 'react';
import { NextIntlClientProvider } from 'next-intl';

const queryClientConfig = {
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: (failureCount: number, error: any) => {
        // Don't retry on 4xx errors
        if (error?.status >= 400 && error?.status < 500) return false;
        return failureCount < 3;
      },
      retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: false,
      onError: (error: any) => {
        console.error('Mutation error:', error);
      },
    },
  },
};

interface ProvidersProps {
  children: ReactNode;
  locale?: string;
  messages?: any;
}

export function Providers({ children, locale = 'en', messages = {} }: ProvidersProps) {
  const [queryClient] = useState(() => new QueryClient(queryClientConfig));

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <QueryClientProvider client={queryClient}>
        {children}
        <ReactQueryDevtools initialIsOpen={false} />
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#393939',
              color: '#fff',
            },
            success: {
              iconTheme: {
                primary: '#24a148',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#da1e28',
                secondary: '#fff',
              },
            },
          }}
        />
      </QueryClientProvider>
    </NextIntlClientProvider>
  );
}