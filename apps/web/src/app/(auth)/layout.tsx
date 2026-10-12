"use client";

import { CheckCircle2, Globe } from "lucide-react";
import { BrandMark } from "@/components/shell";
import { useI18n, useSetLang } from "@/lib/i18n";

const brand = process.env.NEXT_PUBLIC_BRAND_NAME || "Nudgeline";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { t, lang } = useI18n();
  const setLang = useSetLang();
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="hidden flex-col justify-between bg-brand-900 p-12 text-white lg:flex">
        <BrandMark name={brand} light />
        <div className="max-w-md">
          <h1 className="text-3xl font-semibold leading-tight">{t.brandTagline}</h1>
          <p className="mt-4 text-white/70">{t.authPitch}</p>
          <ul className="mt-8 space-y-3">
            {[t.authPoint1, t.authPoint2, t.authPoint3].map((point) => (
              <li key={point} className="flex items-center gap-3 text-white/85">
                <CheckCircle2 className="size-5 text-brand-500" aria-hidden />
                {point}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-white/40">© {new Date().getFullYear()} {brand}</p>
      </section>
      <section className="flex flex-col px-6 py-8 sm:px-12">
        <div className="flex items-center justify-between">
          <div className="lg:invisible">
            <BrandMark name={brand} />
          </div>
          <button
            onClick={() => setLang(lang === "ar" ? "en" : "ar")}
            className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-ink-2 hover:bg-surface"
          >
            <Globe className="size-4" aria-hidden />
            {t.language}
          </button>
        </div>
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-10">{children}</div>
      </section>
    </div>
  );
}
