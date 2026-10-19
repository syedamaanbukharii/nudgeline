"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, ErrorNote, Field, Input } from "@/components/ui";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function LoginPage() {
  const { t } = useI18n();
  const router = useRouter();
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(form: FormData) {
    setLoading(true);
    setError("");
    try {
      await api("/v1/auth/login", { method: "POST", body: { email: form.get("email"), password: form.get("password") } });
      qc.clear();
      router.replace("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : t.somethingWrong);
      setLoading(false);
    }
  }

  return (
    <>
      <h2 className="text-2xl font-semibold tracking-tight">{t.signIn}</h2>
      <form action={submit} className="mt-8 space-y-4">
        {error && <ErrorNote message={error} />}
        <Field label={t.email}>
          <Input name="email" type="email" autoComplete="email" required dir="ltr" />
        </Field>
        <Field label={t.password}>
          <Input name="password" type="password" autoComplete="current-password" required dir="ltr" />
        </Field>
        <Button type="submit" loading={loading} className="w-full">
          {t.signIn}
        </Button>
      </form>
      <p className="mt-6 text-sm text-ink-2">
        {t.noAccount}{" "}
        <Link href="/signup" className="font-medium text-brand-700 hover:underline">
          {t.signUp}
        </Link>
      </p>
    </>
  );
}
