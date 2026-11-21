import { CircleCheck, Info, LoaderCircle, TriangleAlert, X } from "lucide-react";

const cx = (...classes) => classes.filter(Boolean).join(" ");
export { cx };

/** Keep hyphenated terms like "Wi-Fi" and "IoT-Based" from breaking across lines in titles. */
export const keepHyphens = (text) => (text || "").replace(/(\S)-(\S)/g, "$1‑$2");

const VARIANTS = {
  primary: "bg-binding text-binding-ink hover:bg-binding-strong",
  secondary: "border border-rule bg-paper text-ink hover:border-ink-faint",
  ghost: "text-ink-soft hover:bg-rule-soft hover:text-ink",
  danger: "text-redpen hover:bg-redpen-wash",
};
const SIZES = { sm: "h-8 px-2.5 text-[13px] gap-1.5", md: "h-10 px-4 text-sm gap-2", lg: "h-11 px-5 text-[15px] gap-2" };

export function Button({ variant = "primary", size = "md", loading, icon: Icon, children, className, ...props }) {
  return (
    <button
      className={cx(
        "inline-flex shrink-0 items-center justify-center rounded-md font-medium whitespace-nowrap transition-colors",
        "disabled:cursor-not-allowed disabled:opacity-50",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? <LoaderCircle className="size-4 animate-spin" /> : Icon && <Icon className="size-4" />}
      {children}
    </button>
  );
}

/** Small factual tag. Tones are kept few on purpose. */
const TONES = {
  plain: "border-rule text-ink-soft",
  binding: "border-binding/40 text-binding",
  redpen: "border-redpen/40 text-redpen",
};
export function Tag({ tone = "plain", icon: Icon, children, className }) {
  return (
    <span className={cx("inline-flex items-center gap-1 rounded border px-1.5 py-px text-xs", TONES[tone], className)}>
      {Icon && <Icon className="size-3" />}
      {children}
    </span>
  );
}

const LEVELS = ["beginner", "intermediate", "advanced"];
/** Difficulty as a three-step meter with its name, e.g. ▮▮▯ Intermediate. */
export function Difficulty({ level }) {
  const n = LEVELS.indexOf(level) + 1;
  if (!n) return null;
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-ink-soft" title={`Difficulty: ${level}`}>
      <span className="flex gap-0.5" aria-hidden="true">
        {LEVELS.map((_, i) => (
          <span key={i} className={cx("h-2.5 w-1 rounded-[1px]", i < n ? "bg-ink-soft" : "bg-rule")} />
        ))}
      </span>
      {level[0].toUpperCase() + level.slice(1)}
    </span>
  );
}

export function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-ink-soft" role="status">
      <LoaderCircle className="size-4 animate-spin" /> {label}
    </div>
  );
}

const ALERT = {
  error: { icon: TriangleAlert, rule: "border-redpen", text: "text-redpen" },
  warning: { icon: TriangleAlert, rule: "border-foil", text: "text-foil" },
  info: { icon: Info, rule: "border-binding", text: "text-binding" },
  success: { icon: CircleCheck, rule: "border-binding", text: "text-binding" },
};

/** A margin note: a coloured rule on the left instead of a filled box. */
export function Alert({ tone = "info", title, children, action, onClose }) {
  const { icon: Icon, rule, text } = ALERT[tone];
  return (
    <div className={cx("flex gap-3 border-l-2 bg-paper py-3 pr-3 pl-4 text-sm", rule)} role={tone === "error" ? "alert" : "status"}>
      <Icon className={cx("mt-0.5 size-4 shrink-0", text)} />
      <div className="min-w-0 flex-1 text-ink-soft">
        {title && <p className="font-semibold text-ink">{title}</p>}
        {children && <div className={title ? "mt-0.5" : ""}>{children}</div>}
        {action && <div className="mt-3">{action}</div>}
      </div>
      {onClose && (
        <button onClick={onClose} className="shrink-0 text-ink-faint hover:text-ink" aria-label="Dismiss">
          <X className="size-4" />
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="flex flex-col items-start border-t border-rule py-12">
      {Icon && <Icon className="mb-4 size-6 text-ink-faint" />}
      <h3 className="font-serif text-xl font-semibold">{title}</h3>
      {children && <p className="mt-1.5 max-w-md text-[15px] text-ink-soft">{children}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function PageHeader({ title, description, actions }) {
  return (
    <div className="mb-10 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <h1 className="font-serif text-[2rem] leading-tight font-semibold tracking-[-0.01em] sm:text-[2.5rem]">{title}</h1>
        {description && <p className="mt-3 max-w-[60ch] text-[15px] leading-relaxed text-ink-soft">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

/** Link styled as a button (for navigation, keeps semantics right). */
export const linkButton = (variant = "primary", size = "md") =>
  cx("inline-flex items-center justify-center rounded-md font-medium whitespace-nowrap transition-colors", VARIANTS[variant], SIZES[size]);
