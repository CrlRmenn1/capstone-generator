import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { useApp } from "../app-context";
import { Button, cx } from "./ui";
import TitlePage from "./TitlePage";

/** Short welcome shown once to new students (replayable from the Guide). */
const STEPS = [
  {
    title: (name) => `Welcome, ${name}.`,
    body: ["CapSense takes your team from \"we don't have a title yet\" to a Chapter 1 draft you can bring to your adviser.", "Here's how it works, in four short steps."],
    sheet: true,
  },
  {
    title: () => "Describe your team",
    body: ["On Find titles, choose your program, what you'll build with, who it's for, and how ambitious you want to be.", "Add your team's skills and any keywords if you like, then press Suggest titles."],
  },
  {
    title: () => "Compare and save",
    body: [
      "New ideas are ranked by a fit score: how well each matches your choices, and how different it is from existing capstones.",
      "Already done lists similar projects in our records, so you don't propose one that exists. Save the titles your team likes.",
    ],
  },
  {
    title: () => "Draft your Chapter 1",
    body: [
      "Press Develop Chapter 1 on the title you choose. You can edit or rewrite each section, and undo if you change your mind.",
    ],
    note: "Replace every red [cite source] mark with a reference you've checked, then download the draft as Word or PDF.",
  },
  {
    title: () => "AI is optional",
    body: [
      "Everything works with the built-in engine for free. If you want more varied ideas, connect your own Claude, OpenAI, or Gemini key in AI settings. Requests are billed to your key only.",
      "You can replay this tour anytime from the Guide.",
    ],
  },
];

export default function WelcomeTour({ onClose }) {
  const { user } = useApp();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState("from-right");
  const [closing, setClosing] = useState(false);
  const nextRef = useRef(null);
  const current = STEPS[step];
  const last = step === STEPS.length - 1;

  const go = (to) => {
    const target = Math.max(0, Math.min(STEPS.length - 1, to));
    setDirection(target >= step ? "from-right" : "from-left");
    setStep(target);
  };

  // Play the exit animation, then tell the parent.
  const close = (after) => {
    if (closing) return;
    setClosing(true);
    setTimeout(() => {
      onClose();
      after?.();
    }, 160);
  };

  useEffect(() => {
    nextRef.current?.focus();
  }, [step]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") close();
      if (e.key === "ArrowRight") go(step + 1);
      if (e.key === "ArrowLeft") go(step - 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  function finish() {
    close(() => {
      navigate("/");
      setTimeout(() => document.getElementById("preferences")?.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
    });
  }

  return (
    <div className={cx("fixed inset-0 z-40 flex items-end justify-center bg-ink/40 sm:items-center sm:p-4", closing ? "backdrop-out" : "backdrop-in")} onClick={() => close()}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="tour-title"
        className={cx("relative max-h-[92vh] w-full overflow-x-hidden overflow-y-auto bg-paper shadow-2xl sm:max-w-[34rem] sm:rounded-md", closing ? "dialog-out" : "dialog-in")}
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={() => close()} className="absolute top-4 right-4 z-10 p-1 text-ink-faint transition-colors hover:text-ink" aria-label="Close tour">
          <X className="size-4" />
        </button>

        {/* min-h keeps the dialog from resizing between short and long steps. */}
        <div key={step} className={cx("min-h-[21rem] px-7 pt-8 pb-6 sm:px-9", direction)}>
          <p className="text-[13px] text-ink-faint">{step === 0 ? "Getting started" : `Step ${step} of ${STEPS.length - 1}`}</p>
          <h2 id="tour-title" className="mt-2 font-serif text-[1.75rem] leading-tight font-semibold">{current.title(user?.name.split(" ")[0] || "there")}</h2>
          <div className="mt-4 space-y-3 text-[15px] leading-relaxed text-ink-soft">
            {current.body.map((p) => <p key={p}>{p}</p>)}
          </div>
          {current.note && (
            <p className="mt-4 border-l-2 border-redpen pl-3 text-[15px] leading-relaxed text-ink-soft">
              {current.note.split("[cite source]").map((part, i, arr) => (
                <span key={i}>
                  {part}
                  {i < arr.length - 1 && <span className="font-serif text-redpen italic">[cite source]</span>}
                </span>
              ))}
            </p>
          )}
          {current.sheet && (
            <div className="mx-auto mt-6 w-44">
              <TitlePage title="Your capstone title, ready for the panel" program={user?.program} proponents={user?.name} />
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 border-t border-rule px-7 py-4 sm:px-9">
          <div className="flex gap-1.5" aria-hidden="true">
            {STEPS.map((_, i) => (
              <button key={i} onClick={() => go(i)} tabIndex={-1} className={cx("h-1 rounded-full transition-all duration-[var(--dur-slow)] ease-soft", i === step ? "w-5 bg-binding" : "w-1.5 bg-rule")} />
            ))}
          </div>
          <div className="ml-auto flex gap-2">
            {step === 0 ? (
              <Button variant="ghost" size="sm" onClick={() => close()}>Skip</Button>
            ) : (
              <Button variant="ghost" size="sm" onClick={() => go(step - 1)}>Back</Button>
            )}
            {last ? (
              <Button ref={nextRef} size="sm" onClick={finish}>Start finding titles</Button>
            ) : (
              <Button ref={nextRef} size="sm" onClick={() => go(step + 1)}>{step === 0 ? "Show me how" : "Next"}</Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
