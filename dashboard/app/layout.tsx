import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Recall Dashboard",
  description: "Approval and metrics dashboard for Recall",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

