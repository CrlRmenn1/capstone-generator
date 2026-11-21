import { useState } from "react";
import { Link } from "react-router";
import { useApp } from "../app-context";
import { SkeletonRows } from "../components/motion";
import TitlePage from "../components/TitlePage";
import TitleRow from "../components/TitleRow";
import { EmptyState, linkButton, PageHeader } from "../components/ui";
import useTitleActions from "../useTitleActions";

export default function SavedPage() {
  const { user } = useApp();
  const actions = useTitleActions();
  const [selected, setSelected] = useState(null);
  const [expanded, setExpanded] = useState(() => new Set());
  const items = actions.bookmarks.map((b) => ({ id: b.id, ...b.payload, title: b.title, source: b.source }));
  const current = items.find((t) => t.title === selected);

  function toggleRow(title) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else {
        next.add(title);
        setSelected(title);
      }
      return next;
    });
  }

  return (
    <div className="grid gap-x-14 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="min-w-0">
        <PageHeader title="Saved titles" description="Titles your team bookmarked. Open one to compare details or draft its Chapter 1." />
        {!actions.loaded ? (
          <SkeletonRows rows={3} />
        ) : items.length === 0 ? (
          <EmptyState title="Nothing saved yet" action={<Link to="/" className={linkButton()}>Find titles</Link>}>
            Open any suggestion and press Save to keep it here for your team.
          </EmptyState>
        ) : (
          <ol className="border-b border-rule">
            {items.map((item, i) => (
              <TitleRow
                key={item.id}
                index={i}
                rank={i + 1}
                item={item}
                showSource
                expanded={expanded.has(item.title)}
                selected={selected === item.title}
                onToggle={() => toggleRow(item.title)}
                saved
                onToggleSave={actions.toggleSave}
                onDevelop={actions.develop}
                developing={actions.developing === item.title}
              />
            ))}
          </ol>
        )}
      </div>
      <aside className="hidden lg:block" aria-label="Title page preview">
        <div className="sticky top-24">
          <TitlePage title={current?.title} program={user?.program} proponents={user?.name && `${user.name} and team`} note={current?.source === "database" && "Already done"} />
        </div>
      </aside>
    </div>
  );
}
