import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Geronome",
  description: "Geronome — ии-система, которая анализирует биомедицинские данные, выявляет закономерности старения и помогает находить задачи, решение которых ведёт к долголетию",
  icons: {
    icon: [
      { url: "/image.png", sizes: "any" },
      { url: "/image.png", sizes: "128x128", type: "image/png" },
      { url: "/image.png", sizes: "96x96", type: "image/png" },
      { url: "/image.png", sizes: "64x64", type: "image/png" },
      { url: "/image.png", sizes: "48x48", type: "image/png" },
      { url: "/image.png", sizes: "32x32", type: "image/png" },
      { url: "/image.png", sizes: "16x16", type: "image/png" }
    ],
    shortcut: "/image.png",
    apple: "/image.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
