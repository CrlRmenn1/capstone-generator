import { Check, X } from "lucide-react";
import { Link } from "react-router";
import { useApp } from "../app-context";
import { Collapse } from "./motion";
import { cx } from "./ui";

const scrollToForm = () => document.getElementById("preferences")?.scrollIntoView({ behavior: "smooth", block: "start" });

/** First-steps checklist. Each step ticks itself off when the student actually does it. */
export default function GettingStarted() {
  const { user, ai, progress, recordProgress } = useApp();
  if (!user || !progress || progress.checklist_dismissed) return null;

  const steps = [
    { done: progress.generated, title: "Get title ideas", hint: <>Fill in the form below and press <b className="font-medium text-ink">Suggest titles</b>.</>, action: <button onClick={scrollToForm} className="font-medium text-binding underline-offset-2 hover:underline">Go to the form</button> },
    { done: progress.saved, title: "Save the titles you like", hint: <>Open a suggestion and press <b className="font-medium text-ink">Save</b>.</> },
    { done: progress.developed, title: "Draft your Chapter 1", hint: <>Press <b className="font-medium text-ink">Develop Chapter 1</b> on the title your team picks.</> },
    { done: progress.exported, title: "Download it for your adviser", hint: <>Open a draft and download it as Word or PDF.</>, action: <Link to="/outlines" className="font-medium text-binding underline-offset-2 hover:underline">Open my drafts</Link> },
  ];
  const doneCount = steps.filter((s) => s.done).length;
  const next = steps.findIndex((s) => !s.done);

  if (doneCount === steps.length)
    return (
      <div className="mb-10 flex items-center gap-3 border-y border-rule py-3 text-sm">
        <Check className="size-4 text-binding" />
        <p className="flex-1 text-ink-soft">You've done the basics. Keep refining your draft with your team and adviser.</p>
        <button onClick={() => recordProgress("dismiss_checklist")} className="text-ink-faint hover:text-ink">Hide</button>
      </div>
    );

  return (
    <section className="mb-10 border-y border-rule py-5" aria-labelledby="getting-started">
      <div className="mb-4 flex items-baseline gap-3">
        <h2 id="getting-started" className="font-serif text-lg font-semibold">Your first steps</h2>
        <span className="text-sm text-ink-faint">{doneCount} of {steps.length} done</span>
        <Link to="/guide" className="ml-auto text-sm text-ink-soft underline-offset-2 hover:text-ink hover:underline">Read the guide</Link>
        <button onClick={() => recordProgress("dismiss_checklist")} className="text-ink-faint hover:text-ink" aria-label="Hide first steps" title="Hide. You can bring it back from the guide.">
          <X className="size-4" />
        </button>
      </div>
      <ol className="grid gap-x-8 gap-y-4 sm:grid-cols-2">
        {steps.map((s, i) => (
          <li key={s.title} className="flex gap-3">
            <span
              className={cx(
                "mt-0.5 grid size-5 shrink-0 place-items-center rounded-[4px] border text-[11px] font-semibold transition-colors duration-[var(--dur)]",
                s.done ? "border-binding bg-binding text-binding-ink" : i === next ? "border-binding text-binding" : "border-rule text-ink-faint",
              )}
              aria-label={s.done ? "Done" : "Not done yet"}
            >
              {s.done ? <Check className="pop size-3" strokeWidth={3} /> : i + 1}
            </span>
            <div className="min-w-0 text-sm">
              <p className={cx("font-medium transition-colors duration-[var(--dur)]", s.done && "text-ink-faint line-through decoration-ink-faint/60")}>{s.title}</p>
              {/* Hints fold away once a step is done, instead of vanishing. */}
              <Collapse open={!s.done}>
                <p className="mt-0.5 text-ink-soft">{s.hint}</p>
                {i === next && s.action && <p className="mt-1">{s.action}</p>}
              </Collapse>
            </div>
          </li>
        ))}
      </ol>
      {!ai && (
        <p className="mt-5 text-[13px] text-ink-faint">
          Optional: for more varied ideas, <Link to="/settings" className="text-ink-soft underline underline-offset-2 hover:text-ink">add your own AI key</Link>. Everything works without one.
        </p>
      )}
    </section>
  );
}
