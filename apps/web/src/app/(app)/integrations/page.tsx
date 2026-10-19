"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Code2, MessageCircle, Phone, ShoppingBag, type LucideIcon } from "lucide-react";
import { useState } from "react";
import { Forbidden, useCan } from "@/components/shell";
import { Button, Card, CopyField, ErrorNote, Field, Input, Loading, Modal, PageHeader, Pill } from "@/components/ui";
import { api, type IntegrationView } from "@/lib/api";
import { formatDate, useI18n, type TKey } from "@/lib/i18n";

type Provider = IntegrationView["provider"];

const PROVIDERS: Record<Provider, { icon: LucideIcon; fields: { key: string; secret?: boolean; placeholder?: string }[] }> = {
  shopify: {
    icon: ShoppingBag,
    fields: [
      { key: "shop_domain", placeholder: "your-store.myshopify.com" },
      { key: "access_token", secret: true, placeholder: "shpat_…" },
      { key: "webhook_secret", secret: true },
    ],
  },
  webhook: { icon: Code2, fields: [{ key: "callback_url", placeholder: "https://example.com/hooks/outcomes" }] },
  whatsapp: {
    icon: MessageCircle,
    fields: [{ key: "phone_number_id" }, { key: "access_token", secret: true }, { key: "app_secret", secret: true }],
  },
  telephony: { icon: Phone, fields: [{ key: "sip_trunk_id", placeholder: "ST_…" }, { key: "caller_number", placeholder: "+9714…" }] },
};

export default function IntegrationsPage() {
  const { t, lang } = useI18n();
  const can = useCan();
  const [editing, setEditing] = useState<Provider | null>(null);
  const list = useQuery({
    queryKey: ["integrations"],
    queryFn: () => api<IntegrationView[]>("/v1/integrations"),
    enabled: can("integrations.manage"),
  });

  if (!can("integrations.manage")) return <Forbidden />;
  if (!list.data) return <Loading />;

  return (
    <>
      <PageHeader title={t.nav_integrations} />
      <div className="grid gap-4 md:grid-cols-2">
        {list.data.map((item) => {
          const { icon: Icon } = PROVIDERS[item.provider];
          return (
            <Card key={item.provider} className="flex flex-col p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <Icon className="size-5" aria-hidden />
                  </div>
                  <h2 className="font-semibold">{t[`int_${item.provider}` as TKey] as string}</h2>
                </div>
                {item.connected ? (
                  <Pill tone="good">
                    <CheckCircle2 className="me-1 size-3.5" aria-hidden />
                    {t.connected}
                  </Pill>
                ) : (
                  <Pill>{t.notConnected}</Pill>
                )}
              </div>
              <p className="mt-3 text-sm text-ink-2">{t[`int_${item.provider}_desc` as TKey] as string}</p>
              <details className="group mt-3 rounded-lg border border-line bg-page/60 px-3 py-2 text-sm">
                <summary className="cursor-pointer select-none font-medium text-brand-700">{t.howToConnect}</summary>
                <ol className="mt-2 list-decimal space-y-1.5 ps-5 text-ink-2">
                  {(t[`help_${item.provider}` as TKey] as string[]).map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
              </details>
              {item.connected && item.webhook_url && (
                <div className="mt-4 space-y-3">
                  <Field label={t.webhookUrl}>
                    <CopyField value={item.webhook_url} />
                  </Field>
                  {item.reveal &&
                    Object.entries(item.reveal).map(([key, value]) => (
                      <Field key={key} label={t[`f_${key}` as TKey] as string}>
                        <CopyField value={value} />
                      </Field>
                    ))}
                </div>
              )}
              {item.last_event_at && (
                <p className="mt-3 text-xs text-muted">
                  {t.lastEvent}: {formatDate(item.last_event_at, lang)}
                </p>
              )}
              {item.last_error && <div className="mt-3"><ErrorNote message={item.last_error} /></div>}
              <div className="mt-auto flex justify-end pt-5">
                <Button variant={item.connected ? "secondary" : "primary"} size="sm" onClick={() => setEditing(item.provider)}>
                  {item.connected ? t.update : t.connect}
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
      {editing && (
        <IntegrationForm
          item={list.data.find((i) => i.provider === editing)!}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}

function IntegrationForm({ item, onClose }: { item: IntegrationView; onClose: () => void }) {
  const { t } = useI18n();
  const qc = useQueryClient();
  const spec = PROVIDERS[item.provider];
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(spec.fields.filter((f) => !f.secret).map((f) => [f.key, item.config?.[f.key] ?? ""])),
  );
  const done = () => {
    qc.invalidateQueries({ queryKey: ["integrations"] });
    onClose();
  };
  const save = useMutation({
    mutationFn: () => api(`/v1/integrations/${item.provider}`, { method: "PUT", body: values }),
    onSuccess: done,
  });
  const remove = useMutation({
    mutationFn: () => api(`/v1/integrations/${item.provider}`, { method: "DELETE" }),
    onSuccess: done,
  });

  return (
    <Modal open onClose={onClose} title={t[`int_${item.provider}` as TKey] as string}>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        {spec.fields.map((f) => (
          <Field
            key={f.key}
            label={t[`f_${f.key}` as TKey] as string}
            hint={f.secret && item.connected ? `${item.secrets?.[f.key] ?? ""} · ${t.secretKept}` : undefined}
          >
            <Input
              dir="ltr"
              type={f.secret ? "password" : "text"}
              autoComplete="off"
              placeholder={f.placeholder}
              value={values[f.key] ?? ""}
              onChange={(e) => setValues({ ...values, [f.key]: e.target.value })}
            />
          </Field>
        ))}
        {(save.error || remove.error) && <ErrorNote message={(save.error || remove.error)!.message} />}
        <div className="flex items-center justify-between gap-2 pt-2">
          {item.connected ? (
            <Button type="button" variant="danger" size="sm" onClick={() => remove.mutate()} loading={remove.isPending}>
              {t.disconnect}
            </Button>
          ) : (
            <span />
          )}
          <div className="flex gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              {t.cancel}
            </Button>
            <Button type="submit" loading={save.isPending}>
              {item.connected ? t.update : t.connect}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
