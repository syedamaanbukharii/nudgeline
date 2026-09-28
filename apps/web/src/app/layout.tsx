import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nudgeline",
  description: "AI voice agent for sales",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
