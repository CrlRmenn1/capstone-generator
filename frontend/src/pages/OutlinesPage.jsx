import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router";
import { api } from "../api";
import { useApp } from "../app-context";
import { Collapse, SkeletonRows } from "../components/motion";
import { Button, EmptyState, linkButton, PageHeader } from "../components/ui";
import useTitleActions from "../useTitleActions";

const formatDate = (iso) => new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

function OwnTitleForm({ onCancel }) {
  const { meta } = useApp();
  const { develop, developing } = useTitleActions();
  const [form, setForm] = useState({ title: "", domain: "", area: "" });
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  return (
    <form
      className="panel mb-10 space-y-5 p-6"
      onSubmit={(e) => {
        e.preventDefault();
        develop({ title: form.title.trim(), source: "template", context: { domain: form.domain, area: form.area } });
      }}
    >
      <div>
        <h2 className="font-serif text-xl font-semibold">Draft Chapter 1 for your own title</h2>
        <p className="mt-1 text-sm text-ink-soft">If your adviser has already approved a title, type it here exactly as approved.</p>
      </div>
      <label className="block">
        <span className="label">Capstone title</span>
        <input className="input font-serif text-[16px]" value={form.title} onChange={set("title")} required maxLength={300} placeholder="FloodWatch: An IoT-Based Flood Early Warning System with SMS Alerts" />
      </label>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="label">Who it's for</span>
          <select className="input" value={form.domain} onChange={set("domain")} required>
            <option value="">Choose a sector</option>
            {meta.domains.map((d) => <option key={d.key} value={d.key}>{d.label}</option>)}
          </select>
        </label>
        <label className="block">
          <span className="label">Main technology</span>
          <select className="input" value={form.area} onChange={set("area")} required>
            <option value="">Choose a technology</option>
            {meta.technologies.map((t) => <option key={t.key} value={t.key}>{t.label}</option>)}
          </select>
        </label>
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={Boolean(developing)}>Draft Chapter 1</Button>
      </div>
    </form>
  );
}

export default function OutlinesPage() {
  const { toast } = useApp();
  const [outlines, setOutlines] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [removing, setRemoving] = useState(() => new Set());

  useEffect(() => {
    api.get("/outlines").then((d) => setOutlines(d.outlines)).catch(() => setOutlines([]));
  }, []);

  async function remove(outline) {
    if (!window.confirm(`Delete the Chapter 1 draft for "${outline.title}"? This can't be undone.`)) return;
    try {
      await api.del(`/outlines/${outline.id}`);
      // Fold the row away first, then drop it, so the list closes the gap smoothly.
      setRemoving((s) => new Set(s).add(outline.id));
      setTimeout(() => setOutlines((list) => list.filter((o) => o.id !== outline.id)), 400);
      toast("Draft deleted.");
    } catch (err) {
      toast(err.message, "error");
    }
  }

  return (
    <div className="max-w-4xl">
      <PageHeader
        title="Chapter 1 drafts"
        description="Your Introduction drafts for the outline defense. Open one to revise it section by section and download it."
        actions={<Button variant="secondary" onClick={() => setShowForm(!showForm)} aria-expanded={showForm}>Use my own title</Button>}
      />
      <Collapse open={showForm}>
        <OwnTitleForm onCancel={() => setShowForm(false)} />
      </Collapse>
      {outlines === null ? (
        <SkeletonRows rows={3} />
      ) : outlines.length === 0 ? (
        <EmptyState title="No drafts yet" action={<Link to="/" className={linkButton()}>Find a title first</Link>}>
          Press Develop Chapter 1 on any suggestion, or start from a title your adviser already approved.
        </EmptyState>
      ) : (
        <ul className="border-b border-rule">
          {outlines.map((o, i) => (
            <li key={o.id} className="rise" style={{ animationDelay: `${Math.min(i, 10) * 35}ms` }}>
              <Collapse open={!removing.has(o.id)}>
                <div className="group flex items-start gap-4 border-t border-rule py-5">
                  <Link to={`/outlines/${o.id}`} className="min-w-0 flex-1">
                    <p className="font-serif text-[18px] leading-snug transition-colors duration-[var(--dur)] group-hover:text-binding">{o.title}</p>
                    <p className="mt-1 text-[13px] text-ink-faint">
                      {o.mode === "ai" ? "Written with AI" : "Written with the built-in engine"}, last edited {formatDate(o.updated_at)}
                    </p>
                  </Link>
                  <Button variant="ghost" size="sm" icon={Trash2} onClick={() => remove(o)} aria-label={`Delete draft: ${o.title}`} className="hover:text-redpen" />
                </div>
              </Collapse>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
