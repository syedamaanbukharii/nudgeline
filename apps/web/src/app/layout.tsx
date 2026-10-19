import type { Metadata } from "next";
import { IBM_Plex_Sans_Arabic, Inter } from "next/font/google";
import { cookies } from "next/headers";
import { Providers } from "@/components/providers";
import type { Lang } from "@/lib/api";
import "./globals.css";

const latin = Inter({ subsets: ["latin"], variable: "--font-latin", display: "swap" });
const arabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-arabic",
  display: "swap",
});

const brand = process.env.NEXT_PUBLIC_BRAND_NAME || "Nudgeline";

export const metadata: Metadata = {
  title: { default: brand, template: `%s · ${brand}` },
  description: "Automated order-confirmation calls in Arabic and English.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const lang: Lang = (await cookies()).get("lang")?.value === "ar" ? "ar" : "en";
  return (
    <html lang={lang} dir={lang === "ar" ? "rtl" : "ltr"} className={`${latin.variable} ${arabic.variable}`}>
      <body className="min-h-screen font-sans">
        <Providers lang={lang}>{children}</Providers>
      </body>
    </html>
  );
}
