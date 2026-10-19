"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, ErrorNote, Field, Input, Select } from "@/components/ui";
import { api, type Meta } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function SignupPage() {
  const { t, lang } = useI18n();
  const router = useRouter();
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const meta = useQuery({ queryKey: ["meta"], queryFn: () => api<Meta>("/v1/meta") });
  const regionName = new Intl.DisplayNames([lang], { type: "region" });

  async function submit(form: FormData) {
    setLoading(true);
    setError("");
    try {
      await api("/v1/auth/signup", {
        method: "POST",
        body: {
          company_name: form.get("company_name"),
          full_name: form.get("full_name"),
          email: form.get("email"),
          password: form.get("password"),
          country: form.get("country"),
        },
      });
      document.cookie = `lang=${lang}; path=/; max-age=31536000; samesite=lax`;
      qc.clear();
      router.replace("/workflows");
    } catch (e) {
      setError(e instanceof Error ? e.message : t.somethingWrong);
      setLoading(false);
    }
  }

  return (
    <>
      <h2 className="text-2xl font-semibold tracking-tight">{t.signUp}</h2>
      <form action={submit} className="mt-8 space-y-4">
        {error && <ErrorNote message={error} />}
        <Field label={t.companyName}>
          <Input name="company_name" required minLength={2} autoComplete="organization" />
        </Field>
        <Field label={t.fullName}>
          <Input name="full_name" required minLength={2} autoComplete="name" />
        </Field>
        <Field label={t.email}>
          <Input name="email" type="email" required autoComplete="email" dir="ltr" />
        </Field>
        <Field label={t.password} hint={t.passwordHint}>
          <Input name="password" type="password" required minLength={10} autoComplete="new-password" dir="ltr" />
        </Field>
        <Field label={t.country}>
          <Select name="country" defaultValue="AE">
            {(meta.data?.countries ?? [{ code: "AE" }]).map((c) => (
              <option key={c.code} value={c.code}>
                {regionName.of(c.code)}
              </option>
            ))}
          </Select>
        </Field>
        <Button type="submit" loading={loading} className="w-full">
          {t.signUp}
        </Button>
      </form>
      <p className="mt-6 text-sm text-ink-2">
        {t.haveAccount}{" "}
        <Link href="/login" className="font-medium text-brand-700 hover:underline">
          {t.signIn}
        </Link>
      </p>
    </>
  );
}
