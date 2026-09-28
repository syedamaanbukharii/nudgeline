import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Nudgeline Dashboard",
  description: "AI Voice Agent SaaS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased font-sans">
        <div className="flex h-screen flex-col">
          <header className="sticky top-0 z-50 flex h-14 items-center border-b bg-white px-6">
            <h1 className="font-bold">Nudgeline</h1>
          </header>
          <main className="flex-1 overflow-auto p-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
