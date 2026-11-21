import { ChevronDown } from "lucide-react";
import { Link } from "react-router";
import { useApp } from "../app-context";
import { Button, linkButton, PageHeader } from "../components/ui";

const STEPS = [
  ["Describe your team", "On Find titles, choose your program, the technologies you'll build with, who the system is for, and how ambitious you want to be. Add your team's skills and any keywords, then press Suggest titles."],
  ["Compare the suggestions", "Open each new idea to read its summary, objectives, and tools. Check the Already done tab so you don't propose a project that exists. Save the ones your team likes."],
  ["Draft Chapter 1", "Press Develop Chapter 1 on the title you choose. If your adviser already approved a title, go to Chapter 1 drafts and press Use my own title."],
  ["Revise it together", "Rewrite each section in your own words, use Rewrite for new wording, and replace every red [cite source] mark with a reference you have checked."],
  ["Bring it to your adviser", "Download the draft as Word or PDF and consult your adviser before the outline defense."],
];

const TOPICS = [
  {
    title: "Reading your suggestions",
    items: [
      ["Fit score", "Each new idea gets a score out of 100: 60% relevance to your choices and keywords, 40% novelty compared with existing capstones. Ideas that are nearly the same as an existing project are removed."],
      ["Already done", "Capstones in our records that are closest to your choices, with how similar they are. They show what's been done, not what to copy."],
      ["Title page", "On wide screens, the selected title appears on a manuscript title page so you can judge how it reads in print."],
      ["Suggest different titles", "Replaces the list with a new set for the same choices. Save the ones you want first."],
    ],
  },
  {
    title: "Working on your draft",
    items: [
      ["Sections", "Background of the Study, Statement of the Problem, Objectives, Significance, Scope and Limitations, Definition of Terms, and an Overview of the Proposed System."],
      ["Edit", "Leave a blank line between paragraphs. Start a line with \"- \" for a bullet or \"1. \" for a numbered item. Wrap words in **double asterisks** for bold."],
      ["Rewrite and undo", "Rewrite replaces one section's text without touching the others. Undo brings back the version before your last change."],
      ["Problems and objectives", "Each specific problem has a matching objective in the same order. Panels check this, so update both when you change one."],
      ["[cite source]", "Marks a claim that needs evidence. CapSense never invents studies or statistics. Find a real source and replace the mark with your citation."],
    ],
  },
  {
    title: "Built-in engine and AI",
    items: [
      ["Built-in engine", "Free and always available. It uses CapSense's own records and writing templates, so no API key is involved."],
      ["AI", "Optional. In AI settings, choose Claude, OpenAI, or Gemini, paste your own key, and press Test connection. Then pick AI in the switch at the top of the page."],
      ["Cost", "AI requests are billed to your own provider account. Asking the exact same thing twice reuses the first answer."],
      ["Your key", "It's never shown again after you save it. It's forgotten when you log out unless you choose to remember it, in which case it's stored encrypted. You can remove it anytime."],
    ],
  },
];

const FAQ = [
  ["Can we submit the draft as it is?", "No. It gives you structure and wording to start from. Your panel expects your own analysis, real references, and the details of your actual project."],
  ["Our adviser already gave us a title. Can we still use CapSense?", "Yes. Go to Chapter 1 drafts, press Use my own title, type it exactly as approved, and choose the sector and main technology."],
  ["Where did a suggestion go?", "Suggest different titles replaces the whole list. Titles you saved are on the Saved page."],
  ["AI mode shows an error. What should we check?", "In AI settings, press Test connection. The usual causes are a mistyped key, no remaining credit, or a model your key can't use. You can keep working with the built-in engine meanwhile."],
  ["Can my groupmates see my drafts?", "No, drafts and saved titles belong to your account. Share the downloaded Word file, or use one shared team account."],
];

export default function GuidePage() {
  const { user, progress, recordProgress, toast } = useApp();

  return (
    <div className="max-w-3xl">
      <PageHeader
        title="How to use CapSense"
        description="From choosing a capstone title to a Chapter 1 draft you can bring to your adviser."
        actions={
          user && (
            <>
              {progress?.checklist_dismissed && (
                <Button variant="secondary" onClick={async () => { await recordProgress("restore_checklist"); toast("Your first steps are back on Find titles."); }}>Show first steps</Button>
              )}
              <Button variant="secondary" onClick={() => recordProgress("tour_reset")}>Replay the welcome tour</Button>
            </>
          )
        }
      />

      <section className="mb-14">
        <h2 className="mb-5 font-serif text-2xl font-semibold">The five steps</h2>
        <ol className="space-y-5">
          {STEPS.map(([title, text], i) => (
            <li key={title} className="grid grid-cols-[2rem_minmax(0,1fr)] gap-x-3">
              <span className="font-serif text-xl text-ink-faint tabular-nums">{i + 1}</span>
              <div>
                <h3 className="text-[15px] font-semibold">{title}</h3>
                <p className="mt-1 max-w-[65ch] text-[15px] leading-relaxed text-ink-soft">{text}</p>
              </div>
            </li>
          ))}
        </ol>
        <Link to="/" className={`${linkButton()} mt-7 ml-[2.75rem]`}>Start on Find titles</Link>
      </section>

      {TOPICS.map((topic) => (
        <section key={topic.title} className="mb-14">
          <h2 className="mb-2 font-serif text-2xl font-semibold">{topic.title}</h2>
          <dl>
            {topic.items.map(([term, desc]) => (
              <div key={term} className="grid gap-1 border-b border-rule py-4 sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-6">
                <dt className={term === "[cite source]" ? "font-serif text-[15px] text-redpen italic" : "text-[15px] font-medium"}>{term}</dt>
                <dd className="text-[15px] leading-relaxed text-ink-soft">{desc}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}

      <section className="mb-14">
        <h2 className="mb-2 font-serif text-2xl font-semibold">Questions</h2>
        <div>
          {FAQ.map(([q, a]) => (
            <details key={q} className="group border-b border-rule [&_summary::-webkit-details-marker]:hidden">
              <summary className="flex cursor-pointer items-center gap-3 py-4 text-[15px] font-medium">
                <span className="flex-1">{q}</span>
                <ChevronDown className="size-4 shrink-0 text-ink-faint transition-transform group-open:rotate-180" />
              </summary>
              <p className="-mt-1 max-w-[65ch] pb-5 text-[15px] leading-relaxed text-ink-soft">{a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="border-l-2 border-binding pl-5">
        <h2 className="font-serif text-xl font-semibold">Before your outline defense</h2>
        <p className="mt-2 max-w-[65ch] text-[15px] leading-relaxed text-ink-soft">
          Be ready to explain why the problem matters to the people you're serving, why your chosen technique fits, how each objective answers a specific problem, and what your study leaves out. Practise describing the proposed system in your own words.
        </p>
      </section>
    </div>
  );
}
