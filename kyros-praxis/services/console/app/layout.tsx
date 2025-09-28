import type { Metadata } from "next";
// import { Inter } from "next/font/google";  // Commented out to avoid build failures in offline environments
import "./globals.css";
// Carbon Design System global styles
import "@carbon/react/index.scss";
import Providers from "./providers";

// const inter = Inter({ subsets: ["latin"] });  // Commented out to avoid build failures

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
      <body className=""> {/* Removed inter.className to avoid build failures */}
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
