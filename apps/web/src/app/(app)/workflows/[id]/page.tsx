"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Pause, PhoneOutgoing, Play } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Forbidden, useCan } from "@/components/shell";
import {
  Button,
  Card,
  CardHeader,
  ErrorNote,
  Field,
  Input,
  Loading,
  Pill,
  Select,
  SuccessNote,
  Tabs,
  Textarea,
  Toggle,
  cx,
} from "@/components/ui";
import { api, type Lang, type LanguageScript, type Workflow, type WorkflowSettings } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

type Draft = Pick<Workflow, "name" | "default_language" | "script" | "settings">;

function NumberInput({ value, onChange, min, max }: { value: number; onChange: (v: number) => void; min: number; max: number }) {
  return (
    <Input type="number" min={min} max={max} value={value} onChange={(e) => onChange(Number(e.target.value))} className="tabular" />
  );
}

export default function WorkflowEditor() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const can = useCan();
  const qc = useQueryClient();
  const editable = can("workflows.manage");
  const workflow = useQuery({ queryKey: ["workflow", id], queryFn: () => api<Workflow>(`/v1/workflows/${id}`) });
  const [draft, setDraft] = useState<Draft | null>(null);
  const [scriptLang, setScriptLang] = useState<Lang>("ar");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (workflow.data) {
      const { name, default_language, script, settings } = workflow.data;
      setDraft({ name, default_language, script, settings });
    }
  }, [workflow.data]);

  const save = useMutation({
    mutationFn: (body: Draft) => api<Workflow>(`/v1/workflows/${id}`, { method: "PATCH", body }),
    onSuccess: (wf) => {
      qc.setQueryData(["workflow", id], wf);
      qc.invalidateQueries({ queryKey: ["workflows"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    },
  });
  const setStatus = useMutation({
    mutationFn: (action: "activate" | "pause") => api<Workflow>(`/v1/workflows/${id}/${action}`, { method: "POST" }),
    onSuccess: (wf) => {
      qc.setQueryData(["workflow", id], wf);
      qc.invalidateQueries({ queryKey: ["workflows"] });
    },
  });

  if (!can("workflows.view")) return <Forbidden />;
  if (!workflow.data || !draft) return <Loading />;

  const s = draft.settings;
  const setSettings = (patch: Partial<WorkflowSettings>) => setDraft({ ...draft, settings: { ...s, ...patch } });
  const setScript = (key: keyof LanguageScript, value: string) =>
    setDraft({ ...draft, script: { ...draft.script, [scriptLang]: { ...draft.script[scriptLang], [key]: value } } });
  const status = workflow.data.status;
  const statusTone = { active: "good", paused: "warn", draft: "neutral" } as const;

  return (
    <>
      <Link href="/workflows" className="mb-4 inline-flex items-center gap-1.5 text-sm text-ink-2 hover:text-ink">
        <ArrowLeft className="size-4 rtl:rotate-180" aria-hidden /> {t.back}
      </Link>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">{workflow.data.name}</h1>
          <Pill tone={statusTone[status]}>{t[`wf_${status}`]}</Pill>
        </div>
        {editable && (
          <div className="flex gap-2">
            {status === "active" ? (
              <Button variant="secondary" onClick={() => setStatus.mutate("pause")} loading={setStatus.isPending}>
                <Pause className="size-4" aria-hidden /> {t.pause}
              </Button>
            ) : (
              <Button variant="secondary" onClick={() => setStatus.mutate("activate")} loading={setStatus.isPending} title={t.activeNote}>
                <Play className="size-4" aria-hidden /> {t.activate}
              </Button>
            )}
            <Button onClick={() => save.mutate(draft)} loading={save.isPending}>
              {t.save}
            </Button>
          </div>
        )}
      </div>

      <div className="mb-4 space-y-2">
        {save.error && <ErrorNote message={save.error.message} />}
        {setStatus.error && <ErrorNote message={setStatus.error.message} />}
        {saved && <SuccessNote message={t.saved} />}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <div className="grid gap-4 p-5 sm:grid-cols-2">
              <Field label={t.name}>
                <Input value={draft.name} disabled={!editable} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
              </Field>
              <Field label={t.defaultLanguage} hint={draft.default_language === "auto" ? t.langAutoHint : undefined}>
                <Select
                  value={draft.default_language}
                  disabled={!editable}
                  onChange={(e) => setDraft({ ...draft, default_language: e.target.value as Draft["default_language"] })}
                >
                  <option value="auto">{t.lang_auto}</option>
                  <option value="ar">{t.lang_ar}</option>
                  <option value="en">{t.lang_en}</option>
                </Select>
              </Field>
            </div>
          </Card>

          <Card>
            <CardHeader title={t.script} description={<span dir="ltr" className="font-mono text-xs">{t.scriptHint}</span>} />
            <div className="p-5">
              <Tabs
                tabs={[
                  { id: "ar", label: t.lang_ar },
                  { id: "en", label: t.lang_en },
                ]}
                value={scriptLang}
                onChange={setScriptLang}
              />
              <div className="space-y-4">
                {(["prompt", "confirmed", "cancelled", "no_input"] as const).map((key) => (
                  <Field key={key} label={t[`sc_${key}`]}>
                    <Textarea
                      dir={scriptLang === "ar" ? "rtl" : "ltr"}
                      value={draft.script[scriptLang][key]}
                      disabled={!editable}
                      rows={key === "prompt" ? 4 : 2}
                      onChange={(e) => setScript(key, e.target.value)}
                    />
                  </Field>
                ))}
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader title={t.channels} />
            <div className="space-y-6 p-5">
              <div className="space-y-4">
                <Toggle
                  checked={s.whatsapp.enabled}
                  disabled={!editable}
                  onChange={(v) => setSettings({ whatsapp: { ...s.whatsapp, enabled: v } })}
                  label={t.whatsappFirst}
                />
                {s.whatsapp.enabled && (
                  <div className="grid gap-4 ps-14 sm:grid-cols-2">
                    <Field label={t.whatsappTemplate}>
                      <Input
                        dir="ltr"
                        value={s.whatsapp.template_name}
                        disabled={!editable}
                        onChange={(e) => setSettings({ whatsapp: { ...s.whatsapp, template_name: e.target.value } })}
                      />
                    </Field>
                    <Field label={t.waitMinutes}>
                      <NumberInput
                        min={1}
                        max={720}
                        value={s.whatsapp.wait_minutes}
                        onChange={(v) => setSettings({ whatsapp: { ...s.whatsapp, wait_minutes: v } })}
                      />
                    </Field>
                  </div>
                )}
              </div>
              <div className="space-y-4 border-t border-line pt-6">
                <Toggle
                  checked={s.call.enabled}
                  disabled={!editable}
                  onChange={(v) => setSettings({ call: { ...s.call, enabled: v } })}
                  label={t.callStep}
                />
                {s.call.enabled && (
                  <div className="grid gap-4 ps-14 sm:grid-cols-2">
                    <Field label={t.maxAttempts}>
                      <NumberInput min={1} max={6} value={s.call.max_attempts} onChange={(v) => setSettings({ call: { ...s.call, max_attempts: v } })} />
                    </Field>
                    <Field label={t.retryMinutes}>
                      <NumberInput min={5} max={1440} value={s.call.retry_minutes} onChange={(v) => setSettings({ call: { ...s.call, retry_minutes: v } })} />
                    </Field>
                  </div>
                )}
              </div>
              <div className="grid gap-4 border-t border-line pt-6 sm:grid-cols-2">
                <Field label={t.delayMinutes}>
                  <NumberInput min={0} max={1440} value={s.delay_minutes} onChange={(v) => setSettings({ delay_minutes: v })} />
                </Field>
                <div className="flex items-end pb-2">
                  <Toggle checked={s.cod_only} disabled={!editable} onChange={(v) => setSettings({ cod_only: v })} label={t.codOnly} />
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader title={t.callingHours} />
            <div className="space-y-4 p-5">
              <div className="grid max-w-sm grid-cols-2 gap-4">
                <Field label={t.from}>
                  <Input type="time" value={s.window.start} disabled={!editable} onChange={(e) => setSettings({ window: { ...s.window, start: e.target.value } })} />
                </Field>
                <Field label={t.to}>
                  <Input type="time" value={s.window.end} disabled={!editable} onChange={(e) => setSettings({ window: { ...s.window, end: e.target.value } })} />
                </Field>
              </div>
              <div>
                <span className="mb-1.5 block text-sm font-medium">{t.weekdays}</span>
                <div className="flex flex-wrap gap-2">
                  {t.wd.map((label, day) => {
                    const on = s.window.weekdays.includes(day);
                    return (
                      <button
                        key={day}
                        type="button"
                        disabled={!editable}
                        aria-pressed={on}
                        onClick={() =>
                          setSettings({
                            window: {
                              ...s.window,
                              weekdays: on ? s.window.weekdays.filter((d) => d !== day) : [...s.window.weekdays, day].sort(),
                            },
                          })
                        }
                        className={cx(
                          "rounded-lg border px-3 py-1.5 text-sm",
                          on ? "border-brand-500 bg-brand-50 text-brand-700" : "border-line-strong text-ink-2 hover:bg-page",
                        )}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader title={t.afterOutcome} />
            <div className="divide-y divide-line">
              {(["confirmed", "cancelled", "no_response"] as const).map((outcome) => {
                const action = s.actions[outcome];
                const setAction = (patch: Partial<typeof action>) =>
                  setSettings({ actions: { ...s.actions, [outcome]: { ...action, ...patch } } });
                return (
                  <div key={outcome} className="grid items-end gap-4 p-5 sm:grid-cols-[10rem_1fr]">
                    <p className="pb-2.5 text-sm font-medium">{t[`out_${outcome}`]}</p>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field label={t.tagOrder}>
                        <Input dir="ltr" value={action.tag ?? ""} disabled={!editable} onChange={(e) => setAction({ tag: e.target.value || null })} />
                      </Field>
                      {outcome === "cancelled" && (
                        <div className="pb-2">
                          <Toggle checked={action.cancel_order} disabled={!editable} onChange={(v) => setAction({ cancel_order: v })} label={t.cancelInStore} />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        <div className="lg:sticky lg:top-8 lg:self-start">{can("runs.manage") && <TestCall workflowId={id} />}</div>
      </div>
    </>
  );
}

function TestCall({ workflowId }: { workflowId: string }) {
  const { t } = useI18n();
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [lang, setLang] = useState<"" | Lang>("");
  const test = useMutation({
    mutationFn: () =>
      api<{ status: string; run_id: string | null; reason: string | null }>(`/v1/workflows/${workflowId}/test`, {
        method: "POST",
        body: { phone, customer_name: name || "Test", language: lang || null },
      }),
  });
  return (
    <Card>
      <CardHeader title={t.testCall} description={t.testCallHint} />
      <form
        className="space-y-4 p-5"
        onSubmit={(e) => {
          e.preventDefault();
          test.mutate();
        }}
      >
        <Field label={t.phone}>
          <Input dir="ltr" required value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+971 50 123 4567" />
        </Field>
        <Field label={t.customerName}>
          <Input value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label={t.defaultLanguage}>
          <Select value={lang} onChange={(e) => setLang(e.target.value as "" | Lang)}>
            <option value="">{t.lang_auto}</option>
            <option value="ar">{t.lang_ar}</option>
            <option value="en">{t.lang_en}</option>
          </Select>
        </Field>
        {test.error && <ErrorNote message={test.error.message} />}
        {test.data && (
          <SuccessNote
            message={test.data.status === "created" && !test.data.reason ? t.testQueued : `${test.data.status}: ${test.data.reason ?? ""}`}
          />
        )}
        <Button type="submit" className="w-full" loading={test.isPending}>
          <PhoneOutgoing className="size-4" aria-hidden /> {t.call}
        </Button>
        {test.data?.run_id && (
          <Link href={`/orders?run=${test.data.run_id}`} className="block text-center text-sm text-brand-700 hover:underline">
            {t.nav_orders}
          </Link>
        )}
      </form>
    </Card>
  );
}
