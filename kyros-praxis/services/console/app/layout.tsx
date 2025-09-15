import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
// Carbon Design System global styles
import "@carbon/react/index.scss";
import Providers from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Kyros Console",
  description: "Frontend for Kyros Praxis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
