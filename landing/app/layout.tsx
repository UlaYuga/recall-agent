import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

/**
 * Load Inter with Cyrillic subset for correct glyph rendering in Russian copy.
 * next/font/google handles subsetting, caching, and zero-layout-shift loading.
 */
const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Recall — AI Retention Agent",
  description:
    "Event-driven agent that identifies churn risk, generates personalized motion-graphics video with Runway Gen-4.5, routes through human approval, and delivers to dormant players.",
  openGraph: {
    title: "Recall — AI Retention Agent",
    description:
      "Personalized motion-graphics video reactivation pipeline built with Runway Gen-4.5 and ElevenLabs TTS.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
