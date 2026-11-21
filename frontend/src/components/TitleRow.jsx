import { Bookmark, BookmarkCheck, Check, Copy, FileText, Sparkles } from "lucide-react";
import { useState } from "react";
import { useApp } from "../app-context";
import { Button, cx, Difficulty, keepHyphens, Tag } from "./ui";

export const SOURCE_LABEL = { template: "Built-in", ai: "AI", database: "Already done" };

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <Button
      variant="ghost"
      size="sm"
      icon={copied ? Check : Copy}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        } catch {
          /* clipboard blocked */
        }
      }}
    >
      {copied ? "Copied" : "Copy title"}
    </Button>
  );
}

/**
 * One suggestion in a ranked list. Selecting a row expands it and (on wide screens)
 * sets its title on the title page preview.
 */
export default function TitleRow({ item, rank, selected, onSelect, saved, onToggleSave, onDevelop, developing, showSource }) {
  const { meta } = useApp();
  const existing = item.source === "database";
  const areaLabel = meta?.technologies?.find((t) => t.key === item.area)?.label;
  const detailsId = `details-${rank}-${item.title.length}`;

  return (
    <li className={cx("border-t border-rule transition-colors", selected ? "bg-paper" : "hover:bg-paper/60")}>
      <div className={cx("border-l-2", selected ? "border-binding" : "border-transparent")}>
        <button
          type="button"
          onClick={onSelect}
          aria-expanded={selected}
          aria-controls={detailsId}
          className="grid w-full grid-cols-[2rem_minmax(0,1fr)_auto] items-baseline gap-x-3 px-4 py-4 text-left sm:px-5"
        >
          <span className="font-serif text-lg text-ink-faint tabular-nums">{rank}</span>
          <span className="min-w-0">
            <span className={cx("block font-serif text-[17px] leading-snug", selected ? "font-semibold text-ink" : "text-ink")}>{keepHyphens(item.title)}</span>
            <span className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-soft">
              {showSource && <Tag tone={item.source === "ai" ? "binding" : existing ? "redpen" : "plain"} icon={item.source === "ai" ? Sparkles : undefined}>{SOURCE_LABEL[item.source]}</Tag>}
              {!showSource && item.source === "ai" && <Tag tone="binding" icon={Sparkles}>AI</Tag>}
              {areaLabel && <span>{areaLabel}</span>}
              {item.difficulty && <Difficulty level={item.difficulty} />}
              {existing && item.program && <span>{item.program}</span>}
              {existing && item.year && <span>{item.year}</span>}
            </span>
          </span>
          <span className="text-right" title={existing ? "How similar this is to your preferences" : "Fit score: 60% relevance to your choices, 40% novelty"}>
            {existing ? (
              <>
                <span className="block font-serif text-lg tabular-nums">{Math.round((item.similarity || 0) * 100)}%</span>
                <span className="block text-[11px] text-ink-faint">similar</span>
              </>
            ) : item.score !== undefined ? (
              <>
                <span className="block font-serif text-lg tabular-nums">{Math.round(item.score * 100)}</span>
                <span className="block text-[11px] text-ink-faint">fit</span>
              </>
            ) : null}
          </span>
        </button>

        {selected && (
          <div id={detailsId} className="rise px-4 pb-5 sm:pl-[3.75rem] sm:pr-5">
            {item.abstract && <p className="max-w-[68ch] font-serif text-[15.5px] leading-relaxed text-ink-soft">{item.abstract}</p>}
            {existing && item.tech_stack && <p className="mt-2 text-sm text-ink-soft">Built with {item.tech_stack}</p>}
            {existing && (
              <p className="mt-3 text-sm text-ink-soft">This project has already been done. Use it for inspiration, and make sure your proposal is clearly different.</p>
            )}

            {!existing && (item.objectives?.length > 0 || item.stack?.length > 0) && (
              <div className="mt-5 grid gap-6 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
                {item.objectives?.length > 0 && (
                  <section>
                    <h4 className="mb-2 text-sm font-semibold">Suggested objectives</h4>
                    <ol className="list-decimal space-y-1.5 pl-5 text-sm leading-relaxed text-ink-soft marker:text-ink-faint">
                      {item.objectives.map((o, i) => <li key={i}>{o}</li>)}
                    </ol>
                  </section>
                )}
                <div className="space-y-5">
                  {item.stack?.length > 0 && (
                    <section>
                      <h4 className="mb-2 text-sm font-semibold">Tools you could use</h4>
                      <ul className="flex flex-wrap gap-x-3 gap-y-1.5 text-sm text-ink-soft">
                        {item.stack.map((s) => (
                          <li key={s} className={cx(item.matched_stack?.includes(s) && "bg-highlight px-1 text-ink")}>{s}</li>
                        ))}
                      </ul>
                      {item.skill_matches?.length > 0 && <p className="mt-2 text-xs text-ink-faint">Highlighted tools use your team's skills.</p>}
                    </section>
                  )}
                  <section>
                    <h4 className="mb-1 text-sm font-semibold">Why it scored {Math.round(item.score * 100)}</h4>
                    <p className="text-sm text-ink-soft">
                      Relevance {Math.round(item.relevance * 100)}%, novelty {Math.round(item.novelty * 100)}%.
                      {item.closest_existing && <> Closest existing project: <em className="font-serif">{item.closest_existing}</em></>}
                    </p>
                  </section>
                </div>
              </div>
            )}

            <div className="mt-5 flex flex-wrap items-center gap-1">
              {onDevelop && (
                <Button size="sm" icon={FileText} loading={developing} onClick={() => onDevelop(item)} className="mr-1">
                  Develop Chapter 1
                </Button>
              )}
              {onToggleSave && (
                <Button variant="ghost" size="sm" icon={saved ? BookmarkCheck : Bookmark} onClick={() => onToggleSave(item)} className={saved ? "text-binding" : ""}>
                  {saved ? "Saved" : "Save"}
                </Button>
              )}
              <CopyButton text={item.title} />
            </div>
          </div>
        )}
      </div>
    </li>
  );
}
