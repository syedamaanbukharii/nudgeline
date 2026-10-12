"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, PackageCheck } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { OutcomeChart } from "@/components/outcome-chart";
import { Forbidden, useCan, useMe } from "@/components/shell";
import { Button, Card, CardHeader, Empty, ErrorNote, Loading, PageHeader, Select, cx } from "@/components/ui";
import { api, type Overview } from "@/lib/api";
import { formatMoney, useI18n } from "@/lib/i18n";

function pct(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

function Stat({ label, value, hint, emphasis }: { label: string; value: string; hint?: React.ReactNode; emphasis?: boolean }) {
  return (
    <Card className={cx("p-5", emphasis && "border-brand-100 bg-brand-50")}>
      <p className="text-sm text-ink-2">{label}</p>
      <p className={cx("mt-2 text-3xl font-semibold tracking-tight", emphasis ? "text-brand-700" : "text-ink")}>{value}</p>
      {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
    </Card>
  );
}

export default function OverviewPage() {
  const { t, lang } = useI18n();
  const can = useCan();
  const me = useMe();
  const [days, setDays] = useState(7);
  const overview = useQuery({
    queryKey: ["overview", days],
    queryFn: () => api<Overview>(`/v1/overview?days=${days}`),
    enabled: can("runs.view"),
    refetchInterval: 30_000,
  });

  if (!can("runs.view")) return <Forbidden />;

  return (
    <>
      <PageHeader
        title={t.nav_overview}
        description={me.tenant.name}
        action={
          <Select value={days} onChange={(e) => setDays(Number(e.target.value))} className="w-40" aria-label="Range">
            <option value={7}>{t.last7}</option>
            <option value={30}>{t.last30}</option>
          </Select>
        }
      />
      {overview.error && <ErrorNote message={overview.error.message} />}
      {!overview.data ? (
        <Loading />
      ) : overview.data.total === 0 ? (
        <Card>
          <Empty
            icon={PackageCheck}
            title={t.noData}
            hint={t.noDataHint}
            action={
              <Link href="/workflows">
                <Button>
                  {t.getStarted} <ArrowRight className="size-4 rtl:rotate-180" aria-hidden />
                </Button>
              </Link>
            }
          />
        </Card>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label={t.orders} value={String(overview.data.total)} hint={`${t.callMinutes}: ${overview.data.call_minutes}`} />
            <Stat label={t.confirmRate} value={pct(overview.data.confirmation_rate)} />
            <Stat label={t.responseRate} value={pct(overview.data.response_rate)} />
            <Stat
              emphasis
              label={t.savings}
              value={formatMoney(overview.data.estimated_savings, overview.data.currency, lang)}
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
          <Card>
            <CardHeader title={t.outcomesByDay} />
            <div className="p-5">
              <OutcomeChart data={overview.data} />
            </div>
          </Card>
        </div>
      )}
    </>
  );
}
