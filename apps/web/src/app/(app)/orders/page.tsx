"use client";

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageCircle, Phone, PhoneCall, RotateCcw, ShieldCheck, ShieldX, StopCircle } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Forbidden, useCan } from "@/components/shell";
import { Button, Card, Drawer, Empty, ErrorNote, Loading, PageHeader, Pill, Select, StatusBadge } from "@/components/ui";
import { api, type Run, type RunStatus } from "@/lib/api";
import { formatDate, formatMoney, useI18n } from "@/lib/i18n";

const STATUSES: RunStatus[] = ["queued", "waiting", "in_progress", "confirmed", "cancelled", "no_response", "blocked", "failed", "skipped"];
const PAGE = 50;

export default function OrdersPage() {
  return (
    <Suspense fallback={<Loading />}>
      <Orders />
    </Suspense>
  );
}

function Orders() {
  const { t, lang } = useI18n();
  const can = useCan();
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [status, setStatus] = useState<string>("");
  const openRun = params.get("run");

  const runs = useInfiniteQuery({
    queryKey: ["runs", status],
    queryFn: ({ pageParam }) =>
      api<Run[]>(`/v1/runs?limit=${PAGE}${status ? `&status=${status}` : ""}${pageParam ? `&before=${encodeURIComponent(pageParam)}` : ""}`),
    initialPageParam: "",
    getNextPageParam: (last) => (last.length === PAGE ? last[last.length - 1].created_at : undefined),
    enabled: can("runs.view"),
    refetchInterval: 10_000,
  });

  if (!can("runs.view")) return <Forbidden />;
  const setRun = (id: string | null) => router.replace(id ? `${pathname}?run=${id}` : pathname, { scroll: false });
  const rows = runs.data?.pages.flat() ?? [];

  return (
    <>
      <PageHeader
        title={t.nav_orders}
        action={
          <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-48" aria-label={t.status}>
            <option value="">{t.allStatuses}</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {t[`st_${s}`]}
              </option>
            ))}
          </Select>
        }
      />
      {runs.error && <ErrorNote message={runs.error.message} />}
      <Card>
        {!runs.data ? (
          <Loading />
        ) : rows.length === 0 ? (
          <Empty icon={PhoneCall} title={t.noOrders} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-xs text-muted">
                  <th className="px-5 py-3 text-start font-medium">{t.order}</th>
                  <th className="px-5 py-3 text-start font-medium">{t.customer}</th>
                  <th className="px-5 py-3 text-start font-medium">{t.status}</th>
                  <th className="hidden px-5 py-3 text-end font-medium md:table-cell">{t.amount}</th>
                  <th className="hidden px-5 py-3 text-center font-medium sm:table-cell">{t.attempts}</th>
                  <th className="hidden px-5 py-3 text-end font-medium md:table-cell">{t.received}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((run) => (
                  <tr key={run.id} onClick={() => setRun(run.id)} className="cursor-pointer border-b border-line/60 hover:bg-page">
                    <td className="px-5 py-3">
                      <div className="font-medium">{run.order_number || run.external_ref}</div>
                      <div className="text-xs text-muted">{run.source === "test" ? "Test" : run.source}</div>
                    </td>
                    <td className="px-5 py-3">
                      <div>{run.customer_name || "—"}</div>
                      <div className="tabular text-xs text-muted" dir="ltr">
                        {run.phone}
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="tabular hidden px-5 py-3 text-end md:table-cell">{formatMoney(run.total, run.currency || "AED", lang)}</td>
                    <td className="tabular hidden px-5 py-3 text-center sm:table-cell">{run.call_attempts}</td>
                    <td className="hidden px-5 py-3 text-end text-ink-2 md:table-cell">{formatDate(run.created_at, lang)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {runs.hasNextPage && (
              <div className="p-4 text-center">
                <Button variant="secondary" size="sm" onClick={() => runs.fetchNextPage()} loading={runs.isFetchingNextPage}>
                  {t.loadMore}
                </Button>
              </div>
            )}
          </div>
        )}
      </Card>
      <RunDrawer runId={openRun} onClose={() => setRun(null)} />
    </>
  );
}

function RunDrawer({ runId, onClose }: { runId: string | null; onClose: () => void }) {
  const { t, lang } = useI18n();
  const can = useCan();
  const qc = useQueryClient();
  const run = useQuery({
    queryKey: ["run", runId],
    queryFn: () => api<Run>(`/v1/runs/${runId}`),
    enabled: !!runId,
    refetchInterval: (q) => (q.state.data && ["queued", "waiting", "in_progress"].includes(q.state.data.status) ? 4000 : false),
  });
  const action = useMutation({
    mutationFn: (kind: "retry" | "stop") => api(`/v1/runs/${runId}/${kind}`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["run", runId] });
      qc.invalidateQueries({ queryKey: ["runs"] });
    },
  });
  const r = run.data;

  return (
    <Drawer open={!!runId} onClose={onClose} title={r ? r.order_number || r.external_ref : t.order}>
      {!r ? (
        <Loading />
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <StatusBadge status={r.status} />
            {can("runs.manage") && (
              <div className="flex gap-2">
                {r.status !== "in_progress" && (
                  <Button size="sm" variant="secondary" onClick={() => action.mutate("retry")} loading={action.isPending && action.variables === "retry"}>
                    <RotateCcw className="size-4" aria-hidden /> {t.retry}
                  </Button>
                )}
                {["queued", "waiting"].includes(r.status) && (
                  <Button size="sm" variant="danger" onClick={() => action.mutate("stop")} loading={action.isPending && action.variables === "stop"}>
                    <StopCircle className="size-4" aria-hidden /> {t.stop}
                  </Button>
                )}
              </div>
            )}
          </div>
          {action.error && <ErrorNote message={action.error.message} />}

          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
            <Detail label={t.customer} value={r.customer_name || "—"} />
            <Detail label={t.phone} value={<span dir="ltr">{r.phone}</span>} />
            <Detail label={t.amount} value={formatMoney(r.total, r.currency || "AED", lang)} />
            <Detail label={t.defaultLanguage} value={r.language === "ar" ? t.lang_ar : t.lang_en} />
            <Detail label={t.received} value={formatDate(r.created_at, lang)} />
            <Detail label={t.nextAction} value={formatDate(r.next_action_at, lang)} />
            <Detail label={t.source} value={r.source} />
            <Detail label={t.storeUpdate} value={r.actions_status ?? "—"} />
          </dl>
          {r.actions_error && <ErrorNote message={r.actions_error} />}

          {r.items && r.items.length > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-semibold">{t.items}</h3>
              <ul className="space-y-1 text-sm text-ink-2">
                {r.items.map((item, i) => (
                  <li key={i}>
                    {item.quantity} × {item.name}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h3 className="mb-3 text-sm font-semibold">{t.timeline}</h3>
            {r.attempts?.length ? (
              <ol className="space-y-3">
                {r.attempts.map((a) => (
                  <li key={a.id} className="flex gap-3 rounded-lg border border-line p-3">
                    <div className="mt-0.5 text-brand-600">
                      {a.channel === "voice" ? <Phone className="size-4" aria-hidden /> : <MessageCircle className="size-4" aria-hidden />}
                    </div>
                    <div className="min-w-0 flex-1 text-sm">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium">{t[`ch_${a.channel}`]}</span>
                        <Pill>{a.status}</Pill>
                        {a.digit && (
                          <span className="text-ink-2">
                            {t.pressed} <kbd className="rounded border border-line-strong px-1.5 font-mono">{a.digit}</kbd>
                          </span>
                        )}
                        {a.duration_seconds != null && <span className="tabular text-muted">{a.duration_seconds}s</span>}
                      </div>
                      <div className="mt-0.5 text-xs text-muted">{formatDate(a.started_at, lang)}</div>
                      {a.error && <div className="mt-1 break-words text-xs text-critical">{a.error}</div>}
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-muted">—</p>
            )}
          </section>

          {r.compliance_log && r.compliance_log.length > 0 && (
            <section>
              <h3 className="mb-3 text-sm font-semibold">{t.compliance}</h3>
              <ul className="space-y-2 text-sm">
                {r.compliance_log.map((d, i) => (
                  <li key={i} className="flex items-start gap-2">
                    {d.allowed ? (
                      <ShieldCheck className="mt-0.5 size-4 text-good" aria-hidden />
                    ) : (
                      <ShieldX className="mt-0.5 size-4 text-serious" aria-hidden />
                    )}
                    <div>
                      <span className="font-medium">{d.allowed ? t.allowed : t.notAllowed}</span>
                      <span className="text-ink-2"> · {d.reason}</span>
                      <div className="text-xs text-muted">
                        {d.local_time.slice(11, 16)} {t.localTime}
                        {d.retry_at && ` → ${formatDate(d.retry_at, lang)}`}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </Drawer>
  );
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-0.5">{value}</dd>
    </div>
  );
}
