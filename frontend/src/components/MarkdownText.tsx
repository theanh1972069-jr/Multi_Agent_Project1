import React from 'react';

interface MarkdownTextProps {
  content: string;
  className?: string;
}

function renderInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const tokenRegex = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let keyIdx = 0;

  while ((match = tokenRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(
        <strong key={`b-${keyIdx++}`} className="font-semibold text-slate-900">
          {token.slice(2, -2)}
        </strong>,
      );
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(
        <code
          key={`c-${keyIdx++}`}
          className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[0.85em] text-teal-800"
        >
          {token.slice(1, -1)}
        </code>,
      );
    }
    lastIndex = tokenRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

export function MarkdownText({ content, className = '' }: MarkdownTextProps) {
  const lines = content.split(/\r?\n/);
  const blocks: React.ReactNode[] = [];
  let listItems: { ordered: boolean; text: string }[] = [];
  let listOrdered = false;

  const flushList = (keyPrefix: string) => {
    if (listItems.length === 0) return;
    if (listOrdered) {
      blocks.push(
        <ol key={keyPrefix} className="list-decimal space-y-1 pl-5">
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {renderInline(item.text)}
            </li>
          ))}
        </ol>,
      );
    } else {
      blocks.push(
        <ul key={keyPrefix} className="list-disc space-y-1 pl-5">
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {renderInline(item.text)}
            </li>
          ))}
        </ul>,
      );
    }
    listItems = [];
  };

  lines.forEach((rawLine, idx) => {
    const trimmed = rawLine.trim();
    if (!trimmed) {
      flushList(`list-${idx}`);
      return;
    }

    const bulletMatch = /^(?:[-*•])\s+(.*)$/.exec(trimmed);
    const orderedMatch = /^\d+\.\s+(.*)$/.exec(trimmed);
    const headingMatch = /^(#{1,3})\s+(.*)$/.exec(trimmed);

    if (bulletMatch) {
      if (listItems.length > 0 && listOrdered) {
        flushList(`list-${idx}`);
      }
      listOrdered = false;
      listItems.push({ ordered: false, text: bulletMatch[1] });
    } else if (orderedMatch) {
      if (listItems.length > 0 && !listOrdered) {
        flushList(`list-${idx}`);
      }
      listOrdered = true;
      listItems.push({ ordered: true, text: orderedMatch[1] });
    } else if (headingMatch) {
      flushList(`list-${idx}`);
      blocks.push(
        <p key={`h-${idx}`} className="font-bold text-slate-900">
          {renderInline(headingMatch[2])}
        </p>,
      );
    } else {
      flushList(`list-${idx}`);
      blocks.push(
        <p key={`p-${idx}`} className="leading-relaxed">
          {renderInline(trimmed)}
        </p>,
      );
    }
  });

  flushList('list-end');

  return <div className={`space-y-2 ${className}`}>{blocks}</div>;
}
