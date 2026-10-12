"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Lock, PhoneOff, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useCan, useMe } from "@/components/shell";
import {
  Button,
  Card,
  CardHeader,
  Empty,
  ErrorNote,
  Field,
  Input,
  Loading,
  Modal,
  PageHeader,
  Pill,
  Select,
  SuccessNote,
  Tabs,
  Toggle,
} from "@/components/ui";
import { api, type DncEntry, type Meta, type Role, type User } from "@/lib/api";
import { codeLabel, formatDate, useI18n } from "@/lib/i18n";

type Tab = "company" | "team" | "roles" | "dnc";

export default function SettingsPage() {
  const { t } = useI18n();
  const can = useCan();
  const tabs = (
    [
      { id: "company", label: t.company, permission: "settings.manage" },
      { id: "team", label: t.team, permission: "users.manage" },
      { id: "roles", label: t.roles, permission: "roles.manage" },
      { id: "dnc", label: t.dnc, permission: "dnc.manage" },
    ] as const
  ).filter((tab) => can(tab.permission));
  const [tab, setTab] = useState<Tab>(tabs[0]?.id ?? "company");

  return (
    <>
      <PageHeader title={t.nav_settings} />
      {tabs.length === 0 ? (
        <Card className="p-8 text-center text-ink-2">{t.forbidden}</Card>
      ) : (
        <>
          <Tabs tabs={tabs.map(({ id, label }) => ({ id, label }))} value={tab} onChange={setTab} />
          {tab === "company" && <CompanyTab />}
          {tab === "team" && <TeamTab />}
          {tab === "roles" && <RolesTab />}
          {tab === "dnc" && <DncTab />}
        </>
      )}
    </>
  );
}

function CompanyTab() {
  const { t, lang } = useI18n();
  const me = useMe();
  const qc = useQueryClient();
  const meta = useQuery({ queryKey: ["meta"], queryFn: () => api<Meta>("/v1/meta") });
  const [form, setForm] = useState({
    name: me.tenant.name,
    country: me.tenant.country,
    timezone: me.tenant.timezone,
    currency: me.tenant.currency,
    locale: me.tenant.locale,
    avg_return_cost: me.tenant.avg_return_cost || 0,
  });
  const save = useMutation({
    mutationFn: () => api("/v1/tenant", { method: "PATCH", body: form }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["me"] }),
  });
  const regionName = new Intl.DisplayNames([lang], { type: "region" });

  return (
    <Card>
      <form
        className="grid max-w-2xl gap-4 p-5 sm:grid-cols-2"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <Field label={t.companyName} className="sm:col-span-2">
          <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </Field>
        <Field label={t.country}>
          <Select
            value={form.country}
            onChange={(e) => {
              const c = meta.data?.countries.find((x) => x.code === e.target.value);
              setForm({ ...form, country: e.target.value, ...(c ? { timezone: c.timezone, currency: c.currency } : {}) });
            }}
          >
            {(meta.data?.countries ?? [{ code: form.country }]).map((c) => (
              <option key={c.code} value={c.code}>
                {regionName.of(c.code)}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t.timezone}>
          <Input dir="ltr" value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} />
        </Field>
        <Field label={t.currency}>
          <Input dir="ltr" maxLength={3} value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value.toUpperCase() })} />
        </Field>
        <Field label={t.interfaceLanguage}>
          <Select value={form.locale} onChange={(e) => setForm({ ...form, locale: e.target.value as "ar" | "en" })}>
            <option value="ar">{t.lang_ar}</option>
            <option value="en">{t.lang_en}</option>
          </Select>
        </Field>
        <Field label={`${t.avgReturnCost} (${form.currency})`} hint={t.savingsHint} className="sm:col-span-2">
          <Input
            type="number"
            min={0}
            step="0.01"
            className="tabular max-w-48"
            value={form.avg_return_cost}
            onChange={(e) => setForm({ ...form, avg_return_cost: Number(e.target.value) })}
          />
        </Field>
        <div className="space-y-3 sm:col-span-2">
          {save.error && <ErrorNote message={save.error.message} />}
          {save.isSuccess && <SuccessNote message={t.saved} />}
          <Button type="submit" loading={save.isPending}>
            {t.save}
          </Button>
        </div>
      </form>
    </Card>
  );
}

function TeamTab() {
  const { t, lang } = useI18n();
  const me = useMe();
  const qc = useQueryClient();
  const [adding, setAdding] = useState(false);
  const users = useQuery({ queryKey: ["users"], queryFn: () => api<User[]>("/v1/users") });
  const roles = useQuery({ queryKey: ["roles"], queryFn: () => api<Role[]>("/v1/roles") });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<User> }) => api(`/v1/users/${id}`, { method: "PATCH", body }),
    onSettled: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  if (!users.data || !roles.data) return <Loading />;
  return (
    <Card>
      <CardHeader
        title={t.team}
        action={
          <Button size="sm" onClick={() => setAdding(true)}>
            <Plus className="size-4" aria-hidden /> {t.addUser}
          </Button>
        }
      />
      {update.error && (
        <div className="px-5 pt-4">
          <ErrorNote message={update.error.message} />
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-xs text-muted">
              <th className="px-5 py-3 text-start font-medium">{t.fullName}</th>
              <th className="px-5 py-3 text-start font-medium">{t.role}</th>
              <th className="hidden px-5 py-3 text-start font-medium sm:table-cell">{t.lastLogin}</th>
              <th className="px-5 py-3 text-end font-medium">{t.active}</th>
            </tr>
          </thead>
          <tbody>
            {users.data.map((u) => (
              <tr key={u.id} className="border-b border-line/60">
                <td className="px-5 py-3">
                  <div className="font-medium">{u.full_name}</div>
                  <div className="text-xs text-muted">{u.email}</div>
                </td>
                <td className="px-5 py-3">
                  <Select
                    value={u.role_id}
                    className="h-9 w-40"
                    onChange={(e) => update.mutate({ id: u.id, body: { role_id: e.target.value } })}
                  >
                    {roles.data.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                      </option>
                    ))}
                  </Select>
                </td>
                <td className="hidden px-5 py-3 text-ink-2 sm:table-cell">{u.last_login_at ? formatDate(u.last_login_at, lang) : t.never}</td>
                <td className="px-5 py-3">
                  <div className="flex justify-end">
                    <Toggle
                      checked={u.is_active}
                      disabled={u.id === me.user.id}
                      onChange={(v) => update.mutate({ id: u.id, body: { is_active: v } })}
                      label={<span className="sr-only">{t.active}</span>}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {adding && <AddUser roles={roles.data} onClose={() => setAdding(false)} />}
    </Card>
  );
}

function AddUser({ roles, onClose }: { roles: Role[]; onClose: () => void }) {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    role_id: roles.find((r) => r.name === "Operator")?.id ?? roles[roles.length - 1].id,
  });
  const create = useMutation({
    mutationFn: () => api("/v1/users", { method: "POST", body: form }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      onClose();
    },
  });
  return (
    <Modal open onClose={onClose} title={t.addUser}>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <Field label={t.fullName}>
          <Input required minLength={2} value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        </Field>
        <Field label={t.email}>
          <Input required type="email" dir="ltr" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </Field>
        <Field label={t.password} hint={t.passwordHint}>
          <Input required minLength={10} type="password" dir="ltr" autoComplete="new-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </Field>
        <Field label={t.role}>
          <Select value={form.role_id} onChange={(e) => setForm({ ...form, role_id: e.target.value })}>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </Select>
        </Field>
        {create.error && <ErrorNote message={create.error.message} />}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            {t.cancel}
          </Button>
          <Button type="submit" loading={create.isPending}>
            {t.create}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function RolesTab() {
  const { t } = useI18n();
  const [editing, setEditing] = useState<Role | "new" | null>(null);
  const roles = useQuery({ queryKey: ["roles"], queryFn: () => api<Role[]>("/v1/roles") });
  const meta = useQuery({ queryKey: ["meta"], queryFn: () => api<Meta>("/v1/meta") });
  if (!roles.data || !meta.data) return <Loading />;
  return (
    <Card>
      <CardHeader
        title={t.roles}
        action={
          <Button size="sm" onClick={() => setEditing("new")}>
            <Plus className="size-4" aria-hidden /> {t.newRole}
          </Button>
        }
      />
      <ul className="divide-y divide-line">
        {roles.data.map((role) => (
          <li key={role.id} className="flex flex-wrap items-center gap-4 px-5 py-4">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 font-medium">
                {role.name}
                {role.is_system && <Lock className="size-3.5 text-muted" aria-label={t.ownerLocked} />}
              </div>
              <p className="text-sm text-ink-2">{role.is_system ? t.ownerLocked : role.description}</p>
            </div>
            <Pill>
              {role.permissions.length}/{Object.keys(meta.data.permissions).length}
            </Pill>
            {!role.is_system && (
              <Button size="sm" variant="secondary" onClick={() => setEditing(role)}>
                {t.update}
              </Button>
            )}
          </li>
        ))}
      </ul>
      {editing && <RoleForm role={editing === "new" ? null : editing} catalogue={meta.data.permissions} onClose={() => setEditing(null)} />}
    </Card>
  );
}

function RoleForm({ role, catalogue, onClose }: { role: Role | null; catalogue: Record<string, string>; onClose: () => void }) {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [name, setName] = useState(role?.name ?? "");
  const [description, setDescription] = useState(role?.description ?? "");
  const [perms, setPerms] = useState<string[]>(role?.permissions ?? ["runs.view", "workflows.view"]);
  const done = () => {
    qc.invalidateQueries({ queryKey: ["roles"] });
    qc.invalidateQueries({ queryKey: ["me"] });
    onClose();
  };
  const save = useMutation({
    mutationFn: () =>
      role
        ? api(`/v1/roles/${role.id}`, { method: "PATCH", body: { name, description, permissions: perms } })
        : api("/v1/roles", { method: "POST", body: { name, description, permissions: perms } }),
    onSuccess: done,
  });
  const remove = useMutation({ mutationFn: () => api(`/v1/roles/${role!.id}`, { method: "DELETE" }), onSuccess: done });

  return (
    <Modal open onClose={onClose} title={role ? role.name : t.newRole}>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <Field label={t.name}>
          <Input required minLength={2} value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label={t.description}>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} />
        </Field>
        <fieldset>
          <legend className="mb-2 text-sm font-medium">{t.permissions}</legend>
          <div className="max-h-64 space-y-1 overflow-y-auto rounded-lg border border-line p-2">
            {Object.entries(catalogue).map(([key, label]) => (
              <label key={key} className="flex cursor-pointer items-start gap-3 rounded-md px-2 py-1.5 hover:bg-page">
                <input
                  type="checkbox"
                  className="mt-0.5 size-4 accent-brand-600"
                  checked={perms.includes(key)}
                  onChange={(e) => setPerms(e.target.checked ? [...perms, key] : perms.filter((p) => p !== key))}
                />
                <span className="text-sm">
                  <span className="block">{label}</span>
                  <span className="block font-mono text-xs text-muted" dir="ltr">
                    {key}
                  </span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>
        {(save.error || remove.error) && <ErrorNote message={(save.error || remove.error)!.message} />}
        <div className="flex items-center justify-between gap-2">
          {role ? (
            <Button type="button" variant="danger" size="sm" onClick={() => remove.mutate()} loading={remove.isPending}>
              <Trash2 className="size-4" aria-hidden /> {t.delete}
            </Button>
          ) : (
            <span />
          )}
          <div className="flex gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              {t.cancel}
            </Button>
            <Button type="submit" loading={save.isPending}>
              {role ? t.save : t.create}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}

function DncTab() {
  const { t, lang } = useI18n();
  const qc = useQueryClient();
  const [phone, setPhone] = useState("");
  const list = useQuery({ queryKey: ["dnc"], queryFn: () => api<DncEntry[]>("/v1/dnc") });
  const add = useMutation({
    mutationFn: () => api("/v1/dnc", { method: "POST", body: { phone } }),
    onSuccess: () => {
      setPhone("");
      qc.invalidateQueries({ queryKey: ["dnc"] });
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) => api(`/v1/dnc/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dnc"] }),
  });

  return (
    <Card>
      <CardHeader title={t.dnc} description={t.dncHint} />
      <form
        className="flex flex-wrap gap-2 border-b border-line p-5"
        onSubmit={(e) => {
          e.preventDefault();
          add.mutate();
        }}
      >
        <Input dir="ltr" required placeholder="+971 50 123 4567" value={phone} onChange={(e) => setPhone(e.target.value)} className="max-w-xs" />
        <Button type="submit" loading={add.isPending}>
          <Plus className="size-4" aria-hidden /> {t.addNumber}
        </Button>
        {add.error && (
          <div className="w-full">
            <ErrorNote message={add.error.message} />
          </div>
        )}
      </form>
      {!list.data ? (
        <Loading />
      ) : list.data.length === 0 ? (
        <Empty icon={PhoneOff} title={t.noEntries} />
      ) : (
        <ul className="divide-y divide-line">
          {list.data.map((entry) => (
            <li key={entry.id} className="flex items-center gap-4 px-5 py-3 text-sm">
              <span className="tabular flex-1 font-mono" dir="ltr">
                •••• {entry.phone_last4}
              </span>
              <span className="text-ink-2">{codeLabel(t, entry.reason)}</span>
              <span className="hidden text-muted sm:inline">{formatDate(entry.created_at, lang)}</span>
              <Button size="sm" variant="ghost" onClick={() => remove.mutate(entry.id)} aria-label={t.delete}>
                <Trash2 className="size-4" aria-hidden />
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

