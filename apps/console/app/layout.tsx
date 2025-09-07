
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kyros Console",
  description: "Kyros agent console",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
main
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
