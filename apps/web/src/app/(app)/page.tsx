"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ArrowRight, Check, MessageCircle, PackageCheck, PhoneCall, Store } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { OutcomeChart } from "@/components/outcome-chart";
import { Forbidden, useCan, useMe } from "@/components/shell";
import { Card, CardHeader, ErrorNote, Loading, PageHeader, Select, StatusBadge, cx } from "@/components/ui";
import { api, type Overview, type Run, type SetupStatus } from "@/lib/api";
import { codeLabel, formatDate, formatMoney, useI18n } from "@/lib/i18n";

function pct(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

function Stat({
  label,
  value,
  hint,
  tone = "plain",
  href,
}: {
  label: string;
  value: string;
  hint?: React.ReactNode;
  tone?: "plain" | "brand" | "alert";
  href?: string;
}) {
  const body = (
    <Card
      className={cx(
        "h-full p-4 transition-colors sm:p-5",
        tone === "brand" && "border-brand-100 bg-brand-50",
        tone === "alert" && "border-serious/25 bg-serious-bg",
        href && "hover:border-line-strong",
      )}
    >
      <p className="text-sm text-ink-2">{label}</p>
      <p
        className={cx(
          "mt-2 text-2xl font-semibold tracking-tight sm:text-3xl",
          tone === "brand" ? "text-brand-700" : tone === "alert" ? "text-serious" : "text-ink",
        )}
      >
        {value}
      </p>
      {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
    </Card>
  );
  return href ? <Link href={href}>{body}</Link> : body;
}

function SetupChecklist({ setup }: { setup: SetupStatus }) {
  const { t } = useI18n();
  const steps = [
    { done: setup.workflow_created, title: t.step_workflow, hint: t.step_workflow_hint, href: "/workflows" },
    { done: setup.test_call_placed, title: t.step_test, hint: t.step_test_hint, href: "/workflows" },
    { done: setup.store_connected, title: t.step_store, hint: t.step_store_hint, href: "/integrations" },
    { done: setup.workflow_active, title: t.step_active, hint: t.step_active_hint, href: "/workflows" },
    { done: setup.return_cost_set, title: t.step_cost, hint: t.step_cost_hint, href: "/settings" },
  ];
  const done = steps.filter((s) => s.done).length;
  const next = steps.findIndex((s) => !s.done);
  return (
    <Card>
      <div className="flex flex-wrap items-end justify-between gap-3 border-b border-line px-5 py-4">
        <div>
          <h2 className="text-base font-semibold">{t.setupTitle}</h2>
          <p className="mt-0.5 text-sm text-ink-2">{t.setupBody}</p>
        </div>
        <div className="flex min-w-48 items-center gap-3">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-page" role="progressbar" aria-valuenow={done} aria-valuemax={steps.length}>
            <div className="h-full rounded-full bg-brand-500 transition-all" style={{ width: `${(done / steps.length) * 100}%` }} />
          </div>
          <span className="tabular text-sm text-ink-2">
            {done}/{steps.length} {t.stepsDone}
          </span>
        </div>
      </div>
      <ol className="grid gap-px bg-line sm:grid-cols-2 xl:grid-cols-5">
        {steps.map((step, i) => (
          <li key={step.title} className={cx("flex flex-col gap-2 bg-surface p-5", i === next && "bg-brand-50/60")}>
            <span
              className={cx(
                "flex size-7 items-center justify-center rounded-full text-sm font-semibold",
                step.done ? "bg-brand-600 text-white" : i === next ? "bg-brand-100 text-brand-700" : "bg-page text-muted",
              )}
            >
              {step.done ? <Check className="size-4" aria-label={t.stepsDone} /> : i + 1}
            </span>
            <p className={cx("font-medium", step.done && "text-ink-2 line-through decoration-line-strong")}>{step.title}</p>
            <p className="text-sm text-ink-2">{step.hint}</p>
            {!step.done && (
              <Link href={step.href} className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:underline">
                {t.goThere} <ArrowRight className="size-3.5 rtl:rotate-180" aria-hidden />
              </Link>
            )}
          </li>
        ))}
      </ol>
    </Card>
  );
}

function RecentActivity({ runs }: { runs: Run[] }) {
  const { t, lang } = useI18n();
  return (
    <Card className="flex flex-col">
      <CardHeader
        title={t.recentActivity}
        action={
          <Link href="/orders" className="text-sm font-medium text-brand-700 hover:underline">
            {t.viewAll}
          </Link>
        }
      />
      {runs.length === 0 ? (
        <p className="p-5 text-sm text-ink-2">{t.noActivity}</p>
      ) : (
        <ul className="divide-y divide-line">
          {runs.map((run) => (
            <li key={run.id}>
              <Link href={`/orders?run=${run.id}`} className="flex items-center gap-3 px-5 py-3 hover:bg-page">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {run.order_number || run.external_ref}
                    <span className="ms-2 text-xs font-normal text-muted">{codeLabel(t, run.source)}</span>
                  </p>
                  <p className="truncate text-xs text-muted">
                    {run.customer_name || "—"} · {formatDate(run.created_at, lang)}
                  </p>
                </div>
                <StatusBadge status={run.status} />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function HowItWorks() {
  const { t } = useI18n();
  const steps = [
    { icon: Store, text: t.how1 },
    { icon: MessageCircle, text: t.how2 },
    { icon: PhoneCall, text: t.how3 },
    { icon: PackageCheck, text: t.how4 },
  ];
  return (
    <Card className="p-5">
      <h2 className="mb-4 text-base font-semibold">{t.howItWorks}</h2>
      <ol className="space-y-4">
        {steps.map(({ icon: Icon, text }) => (
          <li key={text} className="flex items-start gap-3 text-sm text-ink-2">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
              <Icon className="size-4" aria-hidden />
            </span>
            <span className="pt-1.5">{text}</span>
          </li>
        ))}
      </ol>
    </Card>
  );
}

export default function OverviewPage() {
  const { t, lang } = useI18n();
  const can = useCan();
  const me = useMe();
  const [days, setDays] = useState(7);
  const enabled = can("runs.view");
  const overview = useQuery({
    queryKey: ["overview", days],
    queryFn: () => api<Overview>(`/v1/overview?days=${days}`),
    enabled,
    refetchInterval: 30_000,
  });
  const setup = useQuery({ queryKey: ["setup"], queryFn: () => api<SetupStatus>("/v1/setup"), enabled: can("workflows.view") });
  const recent = useQuery({ queryKey: ["runs", "recent"], queryFn: () => api<Run[]>("/v1/runs?limit=6"), enabled, refetchInterval: 15_000 });

  if (!enabled) return <Forbidden />;

  const o = overview.data;
  const setupDone = setup.data && Object.values(setup.data).every(Boolean);

  return (
    <>
      <PageHeader
        title={t.nav_overview}
        description={t.tagline}
        action={
          <Select value={days} onChange={(e) => setDays(Number(e.target.value))} className="w-40" aria-label={t.last7}>
            <option value={7}>{t.last7}</option>
            <option value={30}>{t.last30}</option>
          </Select>
        }
      />
      {overview.error && <ErrorNote message={overview.error.message} />}
      {!o ? (
        <Loading />
      ) : (
        <div className="space-y-6">
          {setup.data && !setupDone && <SetupChecklist setup={setup.data} />}

          <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
            <Stat label={t.orders} value={String(o.total)} hint={`${t.callMinutes}: ${o.call_minutes}`} />
            <Stat label={t.confirmRate} value={pct(o.confirmation_rate)} hint={`${t.responseRate}: ${pct(o.response_rate)}`} />
            <Stat
              label={t.needsAttention}
              value={String(o.needs_attention)}
              hint={t.needsAttentionHint}
              tone={o.needs_attention > 0 ? "alert" : "plain"}
              href="/orders?status=attention"
            />
            <Stat
              tone="brand"
              label={t.savings}
              value={formatMoney(o.estimated_savings, o.currency, lang)}
              hint={
                me.tenant.avg_return_cost ? (
                  t.savingsHint
                ) : (
                  <Link href="/settings" className="text-brand-700 underline">
                    {t.setReturnCost}
                  </Link>
                )
              }
            />
          </div>

          <div className="grid items-start gap-6 xl:grid-cols-3">
            <Card className="xl:col-span-2">
              <CardHeader title={t.outcomesByDay} />
              <div className="p-5">
                {o.total === 0 ? (
                  <div className="flex flex-col items-center gap-2 py-12 text-center">
                    <AlertCircle className="size-6 text-muted" aria-hidden />
                    <p className="font-medium">{t.noData}</p>
                    <p className="max-w-md text-sm text-ink-2">{t.noDataHint}</p>
                  </div>
                ) : (
                  <OutcomeChart data={o} />
                )}
              </div>
            </Card>
            <div className="space-y-6">
              <RecentActivity runs={recent.data ?? []} />
              {o.total === 0 && <HowItWorks />}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
