import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
// Carbon Design System global styles
import "@carbon/react/index.scss";
import Providers from "./providers";
import { CSPViolationReporter } from "./components/CSPViolationReporter";
import { CSPTester } from "./components/CSPTester";
import { getNonce } from "@/lib/nonce";

const inter = Inter({ 
  subsets: ["latin"],
  display: 'swap',
  fallback: ['system-ui', 'arial']
});

export const metadata: Metadata = {
  title: "Kyros Console",
  description: "Frontend for Kyros Praxis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const nonce = getNonce();

  return (
    <html lang="en">
      <body className={inter.className}>
        <CSPViolationReporter />
        <Providers nonce={nonce}>{children}</Providers>
        <CSPTester />
      </body>
    </html>
  );
}
