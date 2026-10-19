"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Globe, LayoutDashboard, LogOut, Menu, PhoneCall, Plug, Settings, Workflow, X, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { ApiError, api, type Me } from "@/lib/api";
import { roleName, useI18n, useSetLang, type TKey } from "@/lib/i18n";
import { BRAND_NAME, Logo } from "./brand";
import { Loading, cx } from "./ui";

const MeContext = createContext<Me | null>(null);

export function useMe(): Me {
  const me = useContext(MeContext);
  if (!me) throw new Error("useMe outside Shell");
  return me;
}

export function useCan() {
  const me = useMe();
  return (permission: string) => me.permissions.includes(permission);
}

const NAV: { href: string; label: TKey; icon: LucideIcon; permission?: string }[] = [
  { href: "/", label: "nav_overview", icon: LayoutDashboard, permission: "runs.view" },
  { href: "/orders", label: "nav_orders", icon: PhoneCall, permission: "runs.view" },
  { href: "/workflows", label: "nav_workflows", icon: Workflow, permission: "workflows.view" },
  { href: "/integrations", label: "nav_integrations", icon: Plug, permission: "integrations.manage" },
  { href: "/settings", label: "nav_settings", icon: Settings },
];

export function Shell({ children }: { children: ReactNode }) {
  const { t, lang } = useI18n();
  const setLang = useSetLang();
  const router = useRouter();
  const pathname = usePathname();
  const qc = useQueryClient();
  const [menuOpen, setMenuOpen] = useState(false);
  const me = useQuery({ queryKey: ["me"], queryFn: () => api<Me>("/v1/me") });

  useEffect(() => {
    if (me.error instanceof ApiError && me.error.status === 401) router.replace("/login");
  }, [me.error, router]);
  useEffect(() => setMenuOpen(false), [pathname]);

  if (!me.data) return <Loading />;

  const nav = NAV.filter((item) => !item.permission || me.data.permissions.includes(item.permission));
  const signOut = async () => {
    await api("/v1/auth/logout", { method: "POST" }).catch(() => undefined);
    qc.clear();
    router.replace("/login");
  };
  const isActive = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));

  const sidebar = (
    <div className="flex h-full flex-col bg-brand-900 text-white/80">
      <div className="flex h-16 items-center justify-between px-5">
        <Logo size={30} onDark />
        <button className="rounded p-1 hover:bg-white/10 lg:hidden" onClick={() => setMenuOpen(false)} aria-label="Close menu">
          <X className="size-5" />
        </button>
      </div>
      <div className="px-5 pb-5">
        <p className="text-xs text-brand-100/80">{t.catchline}</p>
        <p className="mt-3 truncate rounded-md bg-white/5 px-2.5 py-1.5 text-xs font-medium text-white/80">
          {me.data.tenant.name}
        </p>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cx(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              isActive(href) ? "bg-white/12 text-white" : "hover:bg-white/8 hover:text-white",
            )}
          >
            <Icon className="size-4.5" aria-hidden />
            {t[label] as string}
          </Link>
        ))}
      </nav>
      <div className="space-y-1 border-t border-white/10 p-3">
        <button
          onClick={() => setLang(lang === "ar" ? "en" : "ar")}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-white/8 hover:text-white"
        >
          <Globe className="size-4.5" aria-hidden />
          {t.language}
        </button>
        <button onClick={signOut} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-white/8 hover:text-white">
          <LogOut className="size-4.5" aria-hidden />
          {t.signOut}
        </button>
        <div className="px-3 pt-2 text-xs text-white/50">
          <div className="truncate text-white/80">{me.data.user.full_name}</div>
          <div className="truncate">{roleName(t, me.data.role.name)}</div>
        </div>
      </div>
    </div>
  );

  return (
    <MeContext.Provider value={me.data}>
      <div className="flex min-h-screen flex-col lg:ps-64">
        <aside className="fixed inset-y-0 start-0 z-40 hidden w-64 lg:block">{sidebar}</aside>
        {menuOpen && (
          <div className="fixed inset-0 z-50 bg-ink/40 lg:hidden" onClick={() => setMenuOpen(false)}>
            <aside className="h-full w-64" onClick={(e) => e.stopPropagation()}>
              {sidebar}
            </aside>
          </div>
        )}
        <header className="sticky top-0 z-30 flex h-14 items-center border-b border-line bg-surface px-4 lg:hidden">
          <button onClick={() => setMenuOpen(true)} className="rounded p-1.5 hover:bg-page" aria-label="Open menu">
            <Menu className="size-5" />
          </button>
          <div className="ms-3">
            <Logo size={26} />
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-6 sm:px-6 lg:px-10 lg:py-8">{children}</main>
        <footer className="mx-auto flex w-full max-w-[1440px] flex-wrap items-center justify-between gap-2 border-t border-line px-4 py-4 text-xs text-muted sm:px-6 lg:px-10">
          <span>
            {BRAND_NAME} · {t.catchline}
          </span>
          <span>{t.trustLine}</span>
        </footer>
      </div>
    </MeContext.Provider>
  );
}

export function Forbidden() {
  const { t } = useI18n();
  return <div className="rounded-xl border border-line bg-surface p-8 text-center text-ink-2">{t.forbidden}</div>;
}
