import type { Metadata } from "next";
import "./globals.css";
// Carbon Design System global styles
import "@carbon/react/index.scss";
import Providers from "./providers";

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
      <body className="font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
