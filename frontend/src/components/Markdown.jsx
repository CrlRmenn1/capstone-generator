// Renders the small Markdown subset used by Chapter 1 sections: paragraphs, "- " bullets,
// "1. " numbered items, and **bold**. Content is rendered as React children, never as HTML.
// "[cite source]" is shown the way a panelist would mark it: in red pen.

function inline(text) {
  return text.split(/(\*\*[^*]+\*\*|\[cite source\])/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
    if (part === "[cite source]")
      return (
        <span key={i} className="font-serif whitespace-nowrap text-redpen italic underline decoration-redpen/70 decoration-wavy underline-offset-4" title="Add a verified reference here">
          [cite source]
        </span>
      );
    return part;
  });
}

function toBlocks(content) {
  const blocks = [];
  let para = [];
  const flush = () => {
    if (para.length) blocks.push({ type: "p", text: para.join(" ") });
    para = [];
  };
  for (const raw of content.split("\n")) {
    const line = raw.trim();
    const last = blocks[blocks.length - 1];
    if (!line) flush();
    else if (/^[-*] /.test(line)) {
      flush();
      if (last?.type === "ul") last.items.push(line.slice(2));
      else blocks.push({ type: "ul", items: [line.slice(2)] });
    } else if (/^\d+\. /.test(line)) {
      flush();
      const text = line.replace(/^\d+\. /, "");
      if (last?.type === "ol") last.items.push(text);
      else blocks.push({ type: "ol", items: [text] });
    } else para.push(line);
  }
  flush();
  return blocks;
}

export const countCites = (text) => (text.match(/\[cite source\]/g) || []).length;

export default function Markdown({ content }) {
  return (
    <div className="manuscript space-y-4">
      {toBlocks(content || "").map((block, i) => {
        if (block.type === "ul")
          return (
            <ul key={i} className="list-disc space-y-1.5 pl-7 marker:text-ink-faint">
              {block.items.map((item, j) => <li key={j}>{inline(item)}</li>)}
            </ul>
          );
        if (block.type === "ol")
          return (
            <ol key={i} className="list-decimal space-y-1.5 pl-7 marker:text-ink-soft">
              {block.items.map((item, j) => <li key={j} className="pl-1">{inline(item)}</li>)}
            </ol>
          );
        return <p key={i} className="indent-8">{inline(block.text)}</p>;
      })}
    </div>
  );
}
