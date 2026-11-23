from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

_HEADING_RE = re.compile(r"^\s*(#{1,6})\s*(.+?)\s*$")


def extract_text_from_file(file_path: Path | str) -> str:
    """Extract plain text from `.txt`, `.md`, or `.pdf` files."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md", ".markdown"}:
        return path.read_text(encoding="utf-8", errors="replace").strip()

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        return "\n\n".join(p for p in pages if p).strip()

    raise ValueError(f"Unsupported document extension: {suffix}")


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown/plain text into `(heading, body)` sections."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []

    for line in normalized.split("\n"):
        match = _HEADING_RE.match(line)
        if match:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_heading, body))
            hashes, title = match.groups()
            current_heading = f"{hashes} {title.strip()}"
            current_lines = []
        else:
            current_lines.append(line)

    tail_body = "\n".join(current_lines).strip()
    if tail_body:
        sections.append((current_heading, tail_body))
    elif current_heading and not sections:
        sections.append((current_heading, ""))

    return sections


def _find_split_end(text: str, start: int, max_end: int) -> int:
    """Choose a clean boundary near `max_end` (paragraph, sentence, or whitespace)."""
    if max_end >= len(text):
        return len(text)

    min_end = min(len(text), start + max(80, (max_end - start) // 2))
    window = text[start:max_end]

    for sep in ("\n\n", "\n", ". ", "! ", "? "):
        idx = window.rfind(sep)
        if idx != -1 and start + idx + len(sep) >= min_end:
            return start + idx + len(sep)

    ws_idx = window.rfind(" ")
    if ws_idx != -1 and start + ws_idx >= min_end:
        return start + ws_idx

    return max_end


def chunk_text(
    text: str,
    *,
    source_id: str,
    chunk_size: int = 650,
    overlap: int = 100,
) -> list[dict]:
    """Chunk text into section-aware segments preserving markdown heading context."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")

    sections = _split_sections(text)
    if not sections:
        return []

    chunks: list[dict] = []
    chunk_idx = 0

    for heading, body in sections:
        prefix = f"{heading}\n" if heading else ""
        max_body = max(120, chunk_size - len(prefix))
        effective_overlap = min(overlap, max_body // 2)

        if not body:
            full_text = heading
            chunks.append(
                {
                    "chunk_id": f"{source_id}__chunk_{chunk_idx:04d}",
                    "chunk_index": chunk_idx,
                    "heading": heading,
                    "text": full_text,
                    "content_preview": full_text[:200],
                    "token_estimate": max(1, len(full_text.split())),
                }
            )
            chunk_idx += 1
            continue

        start = 0
        body_len = len(body)
        while start < body_len:
            raw_end = min(body_len, start + max_body)
            end = _find_split_end(body, start, raw_end)
            segment = body[start:end].strip()

            if segment:
                full_text = f"{prefix}{segment}" if prefix else segment
                chunks.append(
                    {
                        "chunk_id": f"{source_id}__chunk_{chunk_idx:04d}",
                        "chunk_index": chunk_idx,
                        "heading": heading,
                        "text": full_text,
                        "content_preview": full_text[:200],
                        "token_estimate": max(1, len(full_text.split())),
                    }
                )
                chunk_idx += 1

            if end >= body_len:
                break

            next_start = max(start + 1, end - effective_overlap)
            # Snap next_start forward to a word boundary if mid-word
            if next_start < body_len and next_start > 0 and not body[next_start - 1].isspace():
                ws = body.find(" ", next_start, end)
                if ws != -1:
                    next_start = ws + 1
            start = next_start

    return chunks
