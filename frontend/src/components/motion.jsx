import { useLayoutEffect, useRef, useState } from "react";
import { cx } from "./ui";

/**
 * Smoothly opens and closes its content by animating grid rows from 0fr to 1fr,
 * so the height is never hard-coded. Closed content stays mounted but is inert.
 */
export function Collapse({ open, children, className }) {
  return (
    <div
      className={cx(
        "grid transition-[grid-template-rows,opacity] duration-[var(--dur-slow)] ease-soft",
        open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
        className,
      )}
      inert={!open}
      aria-hidden={!open}
    >
      <div className="min-h-0 overflow-hidden">{children}</div>
    </div>
  );
}

/**
 * Animates its own height whenever its content's height changes (e.g. a rewritten
 * section, a different tab), instead of letting everything below snap.
 */
export function AutoHeight({ children, className }) {
  const inner = useRef(null);
  const [height, setHeight] = useState(null);

  useLayoutEffect(() => {
    const el = inner.current;
    if (!el) return undefined;
    setHeight(el.offsetHeight);
    const observer = new ResizeObserver(() => setHeight(el.offsetHeight));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      className={cx("transition-[height] duration-[var(--dur-slow)] ease-soft", height !== null && "overflow-hidden", className)}
      style={{ height: height ?? "auto" }}
    >
      <div ref={inner} className="flow-root">{children}</div>
    </div>
  );
}

/** Two labels stacked in one grid cell: the button never changes width when they swap. */
export function SwapLabel({ show, off, on }) {
  return (
    <span className="inline-grid">
      <span className={cx("col-start-1 row-start-1 transition-opacity duration-[var(--dur-fast)]", show ? "opacity-0" : "opacity-100")} aria-hidden={show}>
        {off}
      </span>
      <span className={cx("col-start-1 row-start-1 transition-opacity duration-[var(--dur-fast)]", show ? "opacity-100" : "opacity-0")} aria-hidden={!show}>
        {on}
      </span>
    </span>
  );
}

/** Grey bars in the shape of the content that's loading. */
export function SkeletonLines({ lines = 3, className }) {
  const widths = ["w-11/12", "w-full", "w-4/5", "w-10/12", "w-3/5"];
  return (
    <div className={cx("space-y-3", className)} aria-hidden="true">
      {Array.from({ length: lines }, (_, i) => (
        <div key={i} className={cx("skeleton h-3.5", widths[i % widths.length])} />
      ))}
    </div>
  );
}

export function SkeletonRows({ rows = 4 }) {
  return (
    <div className="border-b border-rule" role="status" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="grid grid-cols-[2rem_minmax(0,1fr)_3rem] gap-x-3 border-t border-rule px-4 py-5 sm:px-5">
          <div className="skeleton h-5 w-4" />
          <div className="space-y-2.5">
            <div className={cx("skeleton h-4", i % 2 ? "w-4/5" : "w-11/12")} />
            <div className="skeleton h-3 w-1/3" />
          </div>
          <div className="skeleton h-5 w-8 justify-self-end" />
        </div>
      ))}
    </div>
  );
}
