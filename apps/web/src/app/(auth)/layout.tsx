"use client";

import { Globe, Languages, Lock, PackageCheck, Plug, ShieldCheck, type LucideIcon } from "lucide-react";
import { BRAND_NAME, Logo } from "@/components/brand";
import { useI18n, useSetLang } from "@/lib/i18n";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { t, lang } = useI18n();
  const setLang = useSetLang();
  const reasons: { icon: LucideIcon; title: string; body: string }[] = [
    { icon: PackageCheck, title: t.why1Title, body: t.why1Body },
    { icon: Languages, title: t.why2Title, body: t.why2Body },
    { icon: ShieldCheck, title: t.why3Title, body: t.why3Body },
    { icon: Plug, title: t.why4Title, body: t.why4Body },
  ];

  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <section className="relative hidden overflow-hidden bg-brand-900 p-10 text-white lg:flex lg:flex-col xl:p-14">
        <div
          aria-hidden
          className="pointer-events-none absolute -end-40 -top-40 size-[520px] rounded-full bg-brand-500/20 blur-3xl"
        />
        <Logo size={36} onDark />
        <div className="relative my-auto max-w-xl py-12">
          <h1 className="text-4xl font-semibold leading-tight tracking-tight xl:text-5xl">{t.catchline}</h1>
          <p className="mt-4 text-lg text-white/75">{t.tagline}</p>
          <ul className="mt-10 grid gap-5 sm:grid-cols-2">
            {reasons.map(({ icon: Icon, title, body }) => (
              <li key={title} className="rounded-xl border border-white/10 bg-white/5 p-4">
                <Icon className="mb-2 size-5 text-brand-100" aria-hidden />
                <p className="font-medium">{title}</p>
                <p className="mt-1 text-sm text-white/65">{body}</p>
              </li>
            ))}
          </ul>
        </div>
        <p className="relative flex items-center gap-2 text-xs text-white/50">
          <Lock className="size-3.5" aria-hidden />
          {t.trustLine}
        </p>
      </section>

      <section className="flex flex-col px-5 py-6 sm:px-10">
        <div className="flex items-center justify-between">
          <span className="lg:invisible">
            <Logo size={30} />
          </span>
          <button
            onClick={() => setLang(lang === "ar" ? "en" : "ar")}
            className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-ink-2 hover:bg-surface"
          >
            <Globe className="size-4" aria-hidden />
            {t.language}
          </button>
        </div>
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-10">
          <div className="mb-8 lg:hidden">
            <p className="text-2xl font-semibold tracking-tight text-brand-700">{t.catchline}</p>
            <p className="mt-1 text-sm text-ink-2">{t.tagline}</p>
          </div>
          {children}
        </div>
        <p className="text-center text-xs text-muted">
          © {new Date().getFullYear()} {BRAND_NAME} · {t.catchline}
        </p>
      </section>
    </div>
  );
}
