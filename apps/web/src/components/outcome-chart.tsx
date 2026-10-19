"use client";

import { useState } from "react";
import type { Overview } from "@/lib/api";
import { formatDate, useI18n } from "@/lib/i18n";
import { cx } from "./ui";

type Key = "confirmed" | "cancelled" | "no_response" | "open";

// Stack order bottom -> top follows the validated categorical order.
const SERIES: { key: Key; color: string; label: "st_confirmed" | "st_cancelled" | "st_no_response" | "st_open" }[] = [
  { key: "confirmed", color: "var(--color-series-confirmed)", label: "st_confirmed" },
  { key: "cancelled", color: "var(--color-series-cancelled)", label: "st_cancelled" },
  { key: "no_response", color: "var(--color-series-noresponse)", label: "st_no_response" },
  { key: "open", color: "var(--color-series-open)", label: "st_open" },
];

interface Day {
  day: string;
  values: Record<Key, number>;
  total: number;
}

function buildDays(data: Overview): Day[] {
  const byDay = new Map(data.series.map((s) => [s.day, s]));
  const days: Day[] = [];
  const today = new Date();
  for (let i = data.days - 1; i >= 0; i--) {
    const d = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - i));
    const key = d.toISOString().slice(0, 10);
    const s = byDay.get(key) ?? { day: key };
    const values: Record<Key, number> = {
      confirmed: s.confirmed ?? 0,
      cancelled: s.cancelled ?? 0,
      no_response: s.no_response ?? 0,
      open: (s.queued ?? 0) + (s.waiting ?? 0) + (s.in_progress ?? 0),
    };
    const other = (s.blocked ?? 0) + (s.failed ?? 0) + (s.skipped ?? 0);
    days.push({ day: key, values, total: Object.values(values).reduce((a, b) => a + b, 0) + other });
  }
  return days;
}

export function OutcomeChart({ data }: { data: Overview }) {
  const { t, lang } = useI18n();
  const [asTable, setAsTable] = useState(false);
  const [hover, setHover] = useState<number | null>(null);
  const days = buildDays(data);
  const max = Math.max(1, ...days.map((d) => SERIES.reduce((sum, s) => sum + d.values[s.key], 0)));
  const height = 200;
  const ticks = [0, Math.ceil(max / 2), max];

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-2">
          {SERIES.map((s) => (
            <li key={s.key} className="flex items-center gap-2">
              <span className="size-2.5 rounded-sm" style={{ background: s.color }} aria-hidden />
              {t[s.label]}
            </li>
          ))}
        </ul>
        <button onClick={() => setAsTable((v) => !v)} className="text-sm font-medium text-brand-700 hover:underline">
          {asTable ? t.showChart : t.showTable}
        </button>
      </div>

      {asTable ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-start text-xs text-muted">
                <th className="py-2 text-start font-medium">{t.day}</th>
                {SERIES.map((s) => (
                  <th key={s.key} className="py-2 text-end font-medium">
                    {t[s.label]}
                  </th>
                ))}
                <th className="py-2 text-end font-medium">{t.total}</th>
              </tr>
            </thead>
            <tbody className="tabular">
              {days.map((d) => (
                <tr key={d.day} className="border-b border-line/60">
                  <td className="py-2">{formatDate(d.day, lang, false)}</td>
                  {SERIES.map((s) => (
                    <td key={s.key} className="py-2 text-end">
                      {d.values[s.key]}
                    </td>
                  ))}
                  <td className="py-2 text-end font-medium">{d.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex gap-3">
          <div className="tabular flex flex-col justify-between pb-6 text-end text-xs text-muted" style={{ height: height + 24 }}>
            {[...ticks].reverse().map((tick) => (
              <span key={tick}>{tick}</span>
            ))}
          </div>
          <div className="relative flex-1">
            <div className="pointer-events-none absolute inset-x-0 top-0" style={{ height }}>
              {ticks.map((tick) => (
                <div
                  key={tick}
                  className={cx("absolute inset-x-0 border-t", tick === 0 ? "border-line-strong" : "border-line")}
                  style={{ bottom: (tick / max) * height }}
                />
              ))}
            </div>
            <div className="relative flex items-end gap-1 sm:gap-2" style={{ height }}>
              {days.map((d, i) => {
                const stacked = SERIES.filter((s) => d.values[s.key] > 0);
                const barTotal = stacked.reduce((sum, s) => sum + d.values[s.key], 0);
                return (
                  <div
                    key={d.day}
                    className="group relative flex h-full flex-1 flex-col justify-end"
                    onMouseEnter={() => setHover(i)}
                    onMouseLeave={() => setHover(null)}
                    onFocus={() => setHover(i)}
                    onBlur={() => setHover(null)}
                    tabIndex={0}
                    aria-label={`${formatDate(d.day, lang, false)}: ${SERIES.map((s) => `${t[s.label]} ${d.values[s.key]}`).join(", ")}`}
                  >
                    {barTotal > 0 && (
                      <span className="tabular mb-1 text-center text-xs text-ink-2">{barTotal}</span>
                    )}
                    <div className="mx-auto flex w-full max-w-10 flex-col-reverse gap-[2px]">
                      {stacked.map((s, idx) => (
                        <div
                          key={s.key}
                          style={{ height: Math.max(2, (d.values[s.key] / max) * height - 2), background: s.color }}
                          className={cx(idx === stacked.length - 1 && "rounded-t", hover !== null && hover !== i && "opacity-50")}
                        />
                      ))}
                    </div>
                    {hover === i && (
                      <div className="absolute bottom-full start-1/2 z-10 mb-2 w-44 -translate-x-1/2 rounded-lg border border-line bg-surface p-3 text-xs shadow-lg rtl:translate-x-1/2">
                        <div className="mb-1.5 font-medium text-ink">{formatDate(d.day, lang, false)}</div>
                        {SERIES.map((s) => (
                          <div key={s.key} className="flex items-center justify-between gap-2 py-0.5 text-ink-2">
                            <span className="flex items-center gap-1.5">
                              <span className="size-2 rounded-sm" style={{ background: s.color }} />
                              {t[s.label]}
                            </span>
                            <span className="tabular text-ink">{d.values[s.key]}</span>
                          </div>
                        ))}
                        <div className="mt-1 flex justify-between border-t border-line pt-1 font-medium text-ink">
                          <span>{t.total}</span>
                          <span className="tabular">{d.total}</span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <div className="mt-2 flex gap-1 sm:gap-2">
              {days.map((d, i) => (
                <span
                  key={d.day}
                  className={cx(
                    "flex-1 truncate text-center text-xs text-muted",
                    days.length > 10 && i % Math.ceil(days.length / 8) !== 0 && "invisible",
                  )}
                >
                  {formatDate(d.day, lang, false)}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
