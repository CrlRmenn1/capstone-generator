import { ArrowLeft, Check, Copy, Download, Pencil, RefreshCw, Undo2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router";
import { api, download } from "../api";
import { useApp } from "../app-context";
import Markdown, { countCites } from "../components/Markdown";
import { Button, cx, EmptyState, keepHyphens, linkButton, Spinner } from "../components/ui";

const SOURCE_NOTE = { template: "", ai: "Written with AI", user: "Edited by you" };

function Section({ outlineId, number, section, onChange }) {
  const { engine, toast } = useApp();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(section.content);
  const [busy, setBusy] = useState(null);
  const [previous, setPrevious] = useState(null);
  const [copied, setCopied] = useState(false);

  async function patch(content, kind, message) {
    setBusy(kind);
    try {
      const { section: updated } = await api.patch(`/outlines/${outlineId}/sections/${section.key}`, { content });
      setPrevious(kind === "undo" ? null : section.content);
      onChange(updated);
      setEditing(false);
      toast(message);
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setBusy(null);
    }
  }

  async function regenerate(engineOverride) {
    if (!engineOverride && section.is_edited && !window.confirm("Rewriting replaces your edits in this section. You can undo it afterwards. Continue?")) return;
    const useEngine = engineOverride || engine;
    setBusy("regen");
    try {
      const { section: updated } = await api.post(`/outlines/${outlineId}/sections/${section.key}/regenerate`, { engine: useEngine });
      setPrevious(section.content);
      onChange(updated);
      toast(`${section.heading} rewritten.`);
    } catch (err) {
      if (err.fallback && useEngine === "ai" && window.confirm(`${err.message}\n\nRewrite it with the built-in engine instead?`)) {
        setBusy(null);
        return regenerate("template");
      }
      toast(err.message, "error");
    } finally {
      setBusy(null);
    }
  }

  const tool = "inline-flex items-center gap-1.5 rounded px-2 py-1 text-[13px] text-ink-faint transition-colors hover:bg-rule-soft hover:text-ink disabled:opacity-50";

  return (
    <section id={`section-${section.key}`} className="scroll-mt-24 border-t border-rule-soft pt-8 first:border-0 first:pt-0">
      <header className="mb-4 flex flex-wrap items-baseline gap-x-3 gap-y-2">
        <h2 className="font-serif text-[19px] font-semibold">
          <span className="mr-2 text-ink-soft tabular-nums">1.{number}</span>
          {section.heading}
        </h2>
        {SOURCE_NOTE[section.source] && <span className="text-[12px] text-binding">{SOURCE_NOTE[section.source]}</span>}
        {!editing && (
          <div className="ml-auto flex flex-wrap gap-0.5 font-sans">
            <button className={tool} onClick={() => { setDraft(section.content); setEditing(true); }}><Pencil className="size-3.5" /> Edit</button>
            <button className={tool} onClick={() => regenerate()} disabled={busy === "regen"}>
              <RefreshCw className={cx("size-3.5", busy === "regen" && "animate-spin")} /> {engine === "ai" ? "Rewrite with AI" : "Rewrite"}
            </button>
            {previous !== null && <button className={tool} onClick={() => patch(previous, "undo", "Change undone.")} disabled={busy === "undo"}><Undo2 className="size-3.5" /> Undo</button>}
            <button
              className={tool}
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(section.content);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 1500);
                } catch {
                  /* blocked */
                }
              }}
            >
              {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />} {copied ? "Copied" : "Copy"}
            </button>
          </div>
        )}
      </header>

      {editing ? (
        <div className="space-y-3 font-sans">
          <textarea
            className="input manuscript min-h-64 !text-[16px]"
            rows={Math.min(28, draft.split("\n").length + 3)}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            maxLength={20000}
            autoFocus
          />
          <p className="text-[13px] text-ink-faint">
            Leave a blank line between paragraphs. Start a line with "- " for a bullet or "1. " for a numbered item. Wrap words in **double asterisks** for bold.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => { setDraft(section.content); setEditing(false); }}>Cancel</Button>
            <Button size="sm" loading={busy === "save"} onClick={() => patch(draft, "save", "Section saved.")}>Save section</Button>
          </div>
        </div>
      ) : (
        <div className={cx("transition-opacity", busy === "regen" && "opacity-40")}>
          <Markdown content={section.content} />
          {(section.key === "problem" || section.key === "objectives") && (
            <p className="mt-4 font-sans text-[13px] text-ink-faint">
              Each specific problem has a matching objective in the same order. If you change one, update the other.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

export default function OutlineEditorPage() {
  const { id } = useParams();
  const { meta, toast, refresh } = useApp();
  const [outline, setOutline] = useState(null);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(null);
  const [active, setActive] = useState(null);

  useEffect(() => {
    api.get(`/outlines/${id}`).then((d) => setOutline(d.outline)).catch(setError);
  }, [id]);

  useEffect(() => {
    if (!outline) return;
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id.replace("section-", ""))),
      { rootMargin: "-25% 0px -65% 0px" },
    );
    outline.sections.forEach((s) => {
      const el = document.getElementById(`section-${s.key}`);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [outline]);

  const cites = useMemo(() => (outline ? outline.sections.reduce((n, s) => n + countCites(s.content), 0) : 0), [outline]);

  if (error)
    return (
      <EmptyState title="This draft isn't available" action={<Link to="/outlines" className={linkButton("secondary")}>Back to my drafts</Link>}>
        {error.message}
      </EmptyState>
    );
  if (!outline) return <Spinner label="Opening draft…" />;

  const updateSection = (updated) => setOutline((o) => ({ ...o, sections: o.sections.map((s) => (s.key === updated.key ? updated : s)) }));

  async function exportAs(format) {
    setExporting(format);
    try {
      await download(`/outlines/${outline.id}/export?format=${format}`);
      refresh();
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setExporting(null);
    }
  }

  const ctx = outline.context || {};
  const label = (list, key) => list?.find((x) => x.key === key)?.label;
  const about = [label(meta?.domains, ctx.domain), label(meta?.technologies, ctx.area)].filter(Boolean).join(", ");

  return (
    <div>
      <Link to="/outlines" className="mb-8 inline-flex items-center gap-1.5 text-sm text-ink-soft hover:text-ink">
        <ArrowLeft className="size-4" /> My drafts
      </Link>

      <div className="mb-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0 max-w-3xl">
          <h1 className="font-serif text-[1.9rem] leading-tight font-semibold tracking-[-0.01em] sm:text-[2.4rem]">{keepHyphens(outline.title)}</h1>
          <p className="mt-3 text-sm text-ink-soft">
            Chapter 1 draft{about && ` for ${about}`}. {outline.mode === "ai" ? "First written with AI." : "First written with the built-in engine."}
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button variant="secondary" icon={Download} loading={exporting === "pdf"} onClick={() => exportAs("pdf")}>Download PDF</Button>
          <Button icon={Download} loading={exporting === "docx"} onClick={() => exportAs("docx")}>Download Word</Button>
        </div>
      </div>

      <div className="grid gap-10 lg:grid-cols-[270px_minmax(0,1fr)]">
        <nav className="hidden lg:block" aria-label="Contents">
          <div className="sticky top-24">
            <h2 className="mb-3 font-serif text-[15px] font-semibold">Contents</h2>
            <ol className="space-y-1">
              {outline.sections.map((s, i) => {
                const n = countCites(s.content);
                return (
                  <li key={s.key}>
                    <a href={`#section-${s.key}`} className={cx("flex items-baseline gap-2 py-1 text-[13.5px] transition-colors", active === s.key ? "text-ink" : "text-ink-soft hover:text-ink")}>
                      <span className="text-ink-faint tabular-nums">1.{i + 1}</span>
                      <span className={cx("min-w-0", active === s.key && "font-medium")}>{s.heading}</span>
                      <span className="min-w-3 flex-1 border-b border-dotted border-ink-faint/50" aria-hidden="true" />
                      {n > 0 ? (
                        <span className="font-serif text-[13px] text-redpen italic" title={`${n} [cite source] left`}>{n}</span>
                      ) : (
                        <Check className="size-3.5 shrink-0 text-ink-faint" aria-label="No citations needed" />
                      )}
                    </a>
                  </li>
                );
              })}
            </ol>
            <p className="mt-5 text-[13px] leading-relaxed text-ink-faint">
              Red numbers count the <span className="font-serif text-redpen italic">[cite source]</span> marks left in each section.
            </p>
          </div>
        </nav>

        <div className="min-w-0">
          <p className="mb-6 max-w-[70ch] text-sm text-ink-soft">
            This is a first draft for your team to rewrite in its own words.{" "}
            {cites > 0 ? (
              <>Replace each of the <span className="text-redpen">{cites} red <span className="font-serif italic">[cite source]</span> marks</span> with a reference you have checked.</>
            ) : (
              "Every citation mark has been replaced."
            )}
          </p>
          <article className="sheet px-6 py-10 sm:px-14 sm:py-16">
            <header className="mb-12 text-center font-serif">
              <p className="text-[17px] font-semibold">CHAPTER I</p>
              <p className="mt-1 text-[17px] font-semibold">INTRODUCTION</p>
            </header>
            <div className="mx-auto max-w-[68ch] space-y-10">
              {outline.sections.map((s, i) => (
                <Section key={s.key} outlineId={outline.id} number={i + 1} section={s} onChange={updateSection} />
              ))}
            </div>
          </article>
        </div>
      </div>
    </div>
  );
}
