import { Check, RefreshCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { useApp } from "../app-context";
import GettingStarted from "../components/GettingStarted";
import { AREA_ICONS, DOMAIN_ICONS, iconFor } from "../components/icons";
import TitlePage from "../components/TitlePage";
import TitleRow from "../components/TitleRow";
import { Alert, Button, cx, Difficulty, EmptyState } from "../components/ui";
import { load, save } from "../storage";
import useTitleActions from "../useTitleActions";

const LEVEL_INFO = {
  beginner: "Well-documented tools and simple features",
  intermediate: "Some integration work or a modest algorithm",
  advanced: "Machine learning, hardware networks, or complex systems",
};
const EMPTY_FORM = { program: "BSIT", interests: [], domain: "", difficulty: "intermediate", skills: "", keywords: "" };
const andList = (items) => new Intl.ListFormat("en", { type: "conjunction" }).format(items);

function Field({ label, hint, children }) {
  return (
    <fieldset className="grid gap-3 border-t border-rule py-6 md:grid-cols-[11rem_minmax(0,1fr)] md:gap-8">
      <legend className="contents">
        <span className="block">
          <span className="block text-[15px] font-semibold">{label}</span>
          {hint && <span className="mt-0.5 block text-[13px] text-ink-faint">{hint}</span>}
        </span>
      </legend>
      <div>{children}</div>
    </fieldset>
  );
}

function Option({ selected, onClick, icon: Icon, children, sub }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cx(
        "relative flex items-start gap-2 rounded-md border px-3 py-2 text-left text-sm transition-colors",
        !Icon && "pr-8",
        selected ? "border-binding bg-binding-wash text-binding" : "border-rule bg-paper text-ink hover:border-ink-faint",
      )}
    >
      {Icon && (selected ? <Check className="mt-0.5 size-4 shrink-0" strokeWidth={2.5} /> : <Icon className="mt-0.5 size-4 shrink-0 text-ink-faint" />)}
      {!Icon && selected && <Check className="absolute top-2.5 right-2.5 size-4" strokeWidth={2.5} />}
      <span className="min-w-0">
        <span className="block font-medium">{children}</span>
        {sub && <span className={cx("block text-xs", selected ? "text-binding/80" : "text-ink-faint")}>{sub}</span>}
      </span>
    </button>
  );
}

export default function GeneratePage() {
  const { meta, engine, ai, user, progress, refresh } = useApp();
  const actions = useTitleActions();
  const [form, setForm] = useState(() => load("capsense.form", EMPTY_FORM, "session"));
  const [result, setResult] = useState(() => load("capsense.result", null, "session"));
  const [tab, setTab] = useState("generated");
  const [selected, setSelected] = useState(() => load("capsense.selected", null, "session"));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const resultsRef = useRef(null);

  useEffect(() => save("capsense.form", form, "session"), [form]);
  useEffect(() => save("capsense.result", result, "session"), [result]);
  useEffect(() => save("capsense.selected", selected, "session"), [selected]);

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const toggleInterest = (key) =>
    set("interests", form.interests.includes(key) ? form.interests.filter((k) => k !== key) : [...form.interests, key]);

  async function run({ seed, engineOverride } = {}) {
    setLoading(true);
    setError(null);
    try {
      const data = await api.post("/titles/generate", { ...form, seed, engine: engineOverride || engine });
      setResult(data);
      setTab("generated");
      setSelected(data.generated[0]?.title || null);
      if (user && !progress?.generated) refresh();
      requestAnimationFrame(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  if (!meta) return <Alert tone="error" title="CapSense can't reach its server">Start the backend with run.py, then reload this page.</Alert>;

  const label = (list, key) => list.find((x) => x.key === key)?.label || key;
  const canSubmit = form.interests.length > 0 && form.domain;
  const lists = result && {
    generated: result.generated,
    recommended: result.recommended.map((r) => ({ ...r, source: "database" })),
  };
  const current = lists ? [...lists.generated, ...lists.recommended].find((t) => t.title === selected) : null;
  const sheetProgram = result?.prefs.program || form.program;

  return (
    <div className="grid gap-x-14 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="min-w-0">
        <header className="mb-10 max-w-[38rem]">
          <h1 className="font-serif text-[2.4rem] leading-[1.1] font-semibold tracking-[-0.015em] sm:text-[3.25rem]">
            Find a capstone title your team can defend.
          </h1>
          <p className="mt-5 text-[16px] leading-relaxed text-ink-soft">
            Describe what your team can build and who it's for. CapSense suggests ranked titles, shows similar projects that already exist, and drafts Chapter 1 for the one you choose.
          </p>
        </header>

        <GettingStarted />

        <form
          id="preferences"
          className="scroll-mt-20"
          onSubmit={(e) => {
            e.preventDefault();
            run();
          }}
        >
          <Field label="Program">
            <div className="grid gap-2 sm:grid-cols-3">
              {meta.programs.map((p) => (
                <Option key={p.key} selected={form.program === p.key} onClick={() => set("program", p.key)} sub={p.label}>{p.key}</Option>
              ))}
            </div>
          </Field>

          <Field label="What you'll build with" hint="Choose one or more">
            <div className="flex flex-wrap gap-2">
              {meta.technologies.map((t) => (
                <Option key={t.key} selected={form.interests.includes(t.key)} onClick={() => toggleInterest(t.key)} icon={iconFor(AREA_ICONS, t.key)}>{t.label}</Option>
              ))}
            </div>
          </Field>

          <Field label="Who it's for" hint="The sector your system will serve">
            <div className="flex flex-wrap gap-2">
              {meta.domains.map((d) => (
                <Option key={d.key} selected={form.domain === d.key} onClick={() => set("domain", d.key)} icon={iconFor(DOMAIN_ICONS, d.key)}>{d.label}</Option>
              ))}
            </div>
          </Field>

          <Field label="How ambitious" hint="Match your team's skills and schedule">
            <div className="grid gap-2 sm:grid-cols-3">
              {meta.levels.map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => set("difficulty", level)}
                  aria-pressed={form.difficulty === level}
                  className={cx(
                    "flex flex-col items-start justify-start rounded-md border px-3 py-2.5 text-left transition-colors",
                    form.difficulty === level ? "border-binding bg-binding-wash" : "border-rule bg-paper hover:border-ink-faint",
                  )}
                >
                  <Difficulty level={level} />
                  <span className="mt-1 block text-xs text-ink-faint">{LEVEL_INFO[level]}</span>
                </button>
              ))}
            </div>
          </Field>

          <Field label="Anything else" hint="Optional">
            <div className="grid gap-4 sm:grid-cols-2">
              <label>
                <span className="label">Your team's skills</span>
                <input className="input" value={form.skills} onChange={(e) => set("skills", e.target.value)} placeholder="PHP, Flutter, Python, Arduino" />
              </label>
              <label>
                <span className="label">Keywords</span>
                <input className="input" value={form.keywords} onChange={(e) => set("keywords", e.target.value)} placeholder="barangay, QR, chatbot, flood" />
              </label>
            </div>
          </Field>

          <div className="flex flex-col-reverse gap-3 border-t border-rule pt-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-[13px] text-ink-faint">
              {engine === "ai" ? `Uses your own ${meta.providers.find((p) => p.key === ai?.provider)?.label || "AI"} key.` : "Uses the built-in engine: free, no API key needed."}
            </p>
            <Button type="submit" size="lg" loading={loading} disabled={!canSubmit}>Suggest titles</Button>
          </div>
        </form>

        <div ref={resultsRef} className="scroll-mt-20">
          {error && (
            <div className="mt-10">
              <Alert
                tone="error"
                title={error.fallback ? "AI mode couldn't suggest titles" : "Couldn't suggest titles"}
                action={error.fallback && <Button variant="secondary" size="sm" onClick={() => run({ engineOverride: "template" })}>Use the built-in engine instead</Button>}
              >
                {error.message}
              </Alert>
            </div>
          )}

          {result && (
            <section className="mt-16" aria-labelledby="suggestions">
              <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 id="suggestions" className="font-serif text-[1.75rem] font-semibold">Suggestions</h2>
                  <p className="mt-1 text-sm text-ink-soft">
                    {result.prefs.program}, {andList(result.prefs.interests.map((k) => label(meta.technologies, k)))}, for {label(meta.domains, result.prefs.domain)}, {result.prefs.difficulty} difficulty.
                  </p>
                </div>
                <Button variant="secondary" icon={RefreshCw} loading={loading} onClick={() => run({ seed: result.seed + 1 })}>Suggest different titles</Button>
              </div>

              <div className="flex gap-6 border-b border-rule" role="tablist">
                {[
                  ["generated", result.engine === "ai" ? "New ideas from AI" : "New ideas", lists.generated.length],
                  ["recommended", "Already done", lists.recommended.length],
                ].map(([key, text, count]) => (
                  <button
                    key={key}
                    role="tab"
                    aria-selected={tab === key}
                    onClick={() => {
                      setTab(key);
                      setSelected(lists[key][0]?.title || null);
                    }}
                    className={cx("-mb-px border-b-2 pb-2.5 text-[15px] transition-colors", tab === key ? "border-binding font-medium text-ink" : "border-transparent text-ink-soft hover:text-ink")}
                  >
                    {text} <span className="text-ink-faint tabular-nums">{count}</span>
                  </button>
                ))}
              </div>

              {tab === "recommended" && (
                <p className="mt-4 mb-1 text-sm text-ink-soft">Capstones in our records that are closest to your choices. Read them for inspiration and to avoid repeating a past project.</p>
              )}

              {lists[tab].length ? (
                <ol className="mt-2 border-b border-rule">
                  {lists[tab].map((item, i) => (
                    <TitleRow
                      key={item.title}
                      rank={i + 1}
                      item={item}
                      selected={selected === item.title}
                      onSelect={() => setSelected(selected === item.title ? null : item.title)}
                      saved={actions.isSaved(item.title)}
                      onToggleSave={actions.toggleSave}
                      onDevelop={actions.develop}
                      developing={actions.developing === item.title}
                    />
                  ))}
                </ol>
              ) : (
                <EmptyState title="No ideas for this combination">Add another technology or choose a different difficulty, then try again.</EmptyState>
              )}
            </section>
          )}
        </div>
      </div>

      <aside className="hidden lg:block" aria-label="Title page preview">
        <div className="sticky top-24">
          <TitlePage
            title={current?.title}
            program={sheetProgram}
            proponents={user?.name && `${user.name} and team`}
            note={current?.source === "database" && `Already done${current.year ? `, ${current.year}` : ""}`}
          />
          <p className="mt-4 text-center text-[13px] text-ink-faint">
            {current ? "How this title would look on your manuscript." : "Select a suggestion to see it on a title page."}
          </p>
        </div>
      </aside>
    </div>
  );
}
