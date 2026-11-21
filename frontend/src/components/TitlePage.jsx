// A capstone manuscript title page, set the way Philippine colleges format them:
// the title in capitals as an inverted pyramid, then the standard presentation lines.

const DEGREES = {
  BSIT: "Bachelor of Science in Information Technology",
  BSCS: "Bachelor of Science in Computer Science",
  BSIS: "Bachelor of Science in Information Systems",
};

/** Break a title into lines that get shorter toward the bottom (inverted pyramid). */
function pyramid(text) {
  const words = text.trim().split(/\s+/);
  const total = text.length;
  const count = Math.max(1, Math.round(total / 24));
  const avg = total / count;
  const lines = [];
  let line = "";
  for (const word of words) {
    const i = lines.length;
    const cap = Math.max(12, avg * (1.3 - (0.55 * i) / Math.max(1, count - 1)));
    const next = line ? `${line} ${word}` : word;
    if (line && next.length > cap) {
      lines.push(line);
      line = word;
    } else line = next;
  }
  if (line) lines.push(line);
  return lines;
}

function splitTitle(title) {
  // A short system name before a colon gets its own line ("ALERTSENSE:").
  const match = /^([^:]{2,40}):\s+(.+)$/.exec(title);
  if (match && match[1].split(" ").length <= 3) return { head: `${match[1]}:`, lines: pyramid(match[2]) };
  return { head: null, lines: pyramid(title) };
}

export default function TitlePage({ title, program = "BSIT", proponents, note, placeholder }) {
  const text = title || "Your capstone title will be set here";
  const { head, lines } = splitTitle(text);
  // Sizes are relative to the sheet's width (cqw), so the page scales as one piece.
  const size = text.length > 120 ? "text-[3.7cqw]" : text.length > 80 ? "text-[4.2cqw]" : "text-[4.7cqw]";
  const now = new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" });

  return (
    <figure className="sheet @container relative mx-auto aspect-[8.5/11] w-full max-w-[380px] select-none" aria-label="Title page preview">
      {note && (
        <span className="absolute top-[5%] right-[6%] -rotate-3 font-serif text-[3.8cqw] text-redpen italic">{note}</span>
      )}
      <div className="flex h-full flex-col items-center px-[12%] pt-[16%] pb-[10%] text-center font-serif text-ink">
        <h2 key={text} className={`typeset font-semibold uppercase ${size} leading-[1.45] ${title ? "" : "text-ink-faint"}`}>
          {head && <span className="block">{head}</span>}
          {lines.map((l, i) => (
            <span key={i} className="block">
              {l}
            </span>
          ))}
        </h2>
        <span className="mt-[6cqw] block h-px w-[14cqw] bg-foil" aria-hidden="true" />

        <div className="mt-auto space-y-[4.5cqw] text-[3.05cqw] leading-[1.55] text-ink-soft">
          <p>
            A Capstone Project
            <br />
            Presented to the Faculty of the
            <br />
            College of Computer Studies
          </p>
          <p>
            In Partial Fulfillment
            <br />
            of the Requirements for the Degree
            <br />
            {DEGREES[program] || DEGREES.BSIT}
          </p>
          <p>
            by
            <br />
            <span className="text-ink">{proponents || "Your team"}</span>
          </p>
        </div>
        <p className="mt-[6cqw] text-[3.05cqw] text-ink-soft">{now}</p>
      </div>
      {placeholder && <figcaption className="sr-only">{placeholder}</figcaption>}
    </figure>
  );
}
