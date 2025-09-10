import './globals.css';
import { Providers } from './providers';
import type { Metadata } from 'next';
import React from 'react';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Kyros Console',
  description: 'Production-grade monorepo console with typed API client',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-blue-600 p-4 text-white">
          <h1 className="text-xl font-bold">Kyros Console</h1>
        </nav>
        <Providers>
          <main className="p-4">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}