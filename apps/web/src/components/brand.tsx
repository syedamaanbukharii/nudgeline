import { useId } from "react";

export const BRAND_NAME = process.env.NEXT_PUBLIC_BRAND_NAME || "Nudgeline";

/** The mark: a confirmation check sending out call waves, i.e. a call that confirms. */
export function LogoMark({ size = 32, className }: { size?: number; className?: string }) {
  const id = useId();
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" className={className} aria-hidden>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#17a07c" />
          <stop offset="1" stopColor="#0b5c48" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill={`url(#${id})`} />
      <path d="M8.5 16.5 13.5 21.5 23 12" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M23.6 8.65a3.4 3.4 0 0 1 2.75 2.76" stroke="#fff" strokeOpacity=".85" strokeWidth="2" strokeLinecap="round" />
      <path d="M24.1 5.7a6.4 6.4 0 0 1 5.2 5.19" stroke="#fff" strokeOpacity=".5" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** Mark + wordmark. "line" takes the brand green; on dark surfaces the whole word is white. */
export function Logo({ size = 32, onDark = false }: { size?: number; onDark?: boolean }) {
  const split = BRAND_NAME === "Nudgeline";
  return (
    <span className="inline-flex items-center gap-2.5" dir="ltr">
      <LogoMark size={size} />
      <span
        className={onDark ? "font-semibold tracking-tight text-white" : "font-semibold tracking-tight text-ink"}
        style={{ fontSize: size * 0.6 }}
      >
        {split ? (
          <>
            Nudge<span className={onDark ? "text-brand-100" : "text-brand-600"}>line</span>
          </>
        ) : (
          BRAND_NAME
        )}
      </span>
    </span>
  );
}
