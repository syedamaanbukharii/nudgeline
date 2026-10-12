"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, CalendarCheck, ShoppingBag, Workflow as WorkflowIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Forbidden, useCan, useMe } from "@/components/shell";
import { Button, Card, CardHeader, ErrorNote, Loading, PageHeader, Pill } from "@/components/ui";
import { api, type Template, type Workflow } from "@/lib/api";
import { dictionaries, formatDate, formatMoney, useI18n } from "@/lib/i18n";

type Dict = (typeof dictionaries)["en"];

function triggerSummary(wf: Workflow, t: Dict, currency: string, lang: "ar" | "en"): string[] {
  const trigger = wf.settings.trigger;
  if (!trigger) return [];
  const labels = trigger.payment_types.map((p) => t[`pay_${p}`].split(" (")[0]);
  if (trigger.min_total) labels.push(`≥ ${formatMoney(trigger.min_total, currency, lang)}`);
  if (trigger.new_customers_only) labels.push(t.newCustomersOnly);
  return labels;
}

const INDUSTRY_ICON = { ecommerce: ShoppingBag, healthcare: CalendarCheck } as const;

export default function WorkflowsPage() {
  const { t, lang } = useI18n();
  const can = useCan();
  const me = useMe();
  const router = useRouter();
  const qc = useQueryClient();
  const workflows = useQuery({ queryKey: ["workflows"], queryFn: () => api<Workflow[]>("/v1/workflows"), enabled: can("workflows.view") });
  const templates = useQuery({ queryKey: ["templates"], queryFn: () => api<Template[]>("/v1/templates"), enabled: can("workflows.view") });
  const create = useMutation({
    mutationFn: (key: string) => api<Workflow>("/v1/workflows", { method: "POST", body: { template_key: key } }),
    onSuccess: (wf) => {
      qc.invalidateQueries({ queryKey: ["workflows"] });
      router.push(`/workflows/${wf.id}`);
    },
  });

  if (!can("workflows.view")) return <Forbidden />;
  if (!workflows.data || !templates.data) return <Loading />;

  const statusTone = { active: "good", paused: "warn", draft: "neutral" } as const;

  return (
    <>
      <PageHeader title={t.nav_workflows} />
      {create.error && <ErrorNote message={create.error.message} />}

      {workflows.data.length > 0 && (
        <Card className="mb-8">
          <ul className="divide-y divide-line">
            {workflows.data.map((wf) => (
              <li key={wf.id}>
                <Link href={`/workflows/${wf.id}`} className="flex items-center gap-4 px-5 py-4 hover:bg-page">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <WorkflowIcon className="size-5" aria-hidden />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-ink">{wf.name}</p>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {triggerSummary(wf, t, me.tenant.currency, lang).map((label) => (
                        <span key={label} className="rounded-md bg-page px-2 py-0.5 text-xs text-ink-2">
                          {label}
                        </span>
                      ))}
                      <span className="px-1 py-0.5 text-xs text-muted">{formatDate(wf.updated_at, lang)}</span>
                    </div>
                  </div>
                  <Pill tone={statusTone[wf.status]}>{t[`wf_${wf.status}`]}</Pill>
                  <ArrowRight className="size-4 text-muted rtl:rotate-180" aria-hidden />
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">{t.templates}</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {templates.data.map((tpl) => {
          const Icon = INDUSTRY_ICON[tpl.industry as keyof typeof INDUSTRY_ICON] ?? WorkflowIcon;
          return (
            <Card key={tpl.key} className="flex flex-col">
              <CardHeader
                title={
                  <span className="flex items-center gap-2">
                    <Icon className="size-5 text-brand-600" aria-hidden />
                    {tpl.name[lang]}
                  </span>
                }
                action={!tpl.available && <Pill>{t.comingSoon}</Pill>}
              />
              <div className="flex flex-1 flex-col justify-between gap-4 p-5">
                <p className="text-sm text-ink-2">{tpl.description[lang]}</p>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex gap-2">
                    {tpl.options.map((o) => (
                      <span key={o.digit} className="inline-flex items-center gap-1.5 text-xs text-ink-2">
                        <kbd className="flex size-6 items-center justify-center rounded border border-line-strong bg-page font-mono text-ink">
                          {o.digit}
                        </kbd>
                        {o.label[lang]}
                      </span>
                    ))}
                  </div>
                  {can("workflows.manage") && tpl.available && (
                    <Button size="sm" loading={create.isPending && create.variables === tpl.key} onClick={() => create.mutate(tpl.key)}>
                      {t.useTemplate}
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </>
  );
}
