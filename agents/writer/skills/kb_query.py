"""Knowledge Base Query Skill

Searches the writer agent's local knowledge base for relevant documents.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class KBResult:
    path: str
    score: float
    excerpt: str
    section: str


KB_ROOT = Path(__file__).parent.parent / "knowledge-base"


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r'[a-zA-Z\u4e00-\u9fff]+', text.lower()))


def _score(query_tokens: set[str], content: str) -> float:
    content_tokens = _tokenize(content)
    if not query_tokens:
        return 0.0
    return len(query_tokens & content_tokens) / len(query_tokens)


def query(query_text: str, top_k: int = 3) -> List[KBResult]:
    """Search knowledge base for documents relevant to query_text."""
    tokens = _tokenize(query_text)
    results: List[KBResult] = []

    for md_file in KB_ROOT.rglob("*.md"):
        if md_file.name == "README.md":
            continue
        content = md_file.read_text(encoding="utf-8")
        score = _score(tokens, content)
        if score > 0:
            # Extract first relevant excerpt (up to 300 chars)
            lines = content.splitlines()
            excerpt_lines = []
            for line in lines:
                if any(t in line.lower() for t in tokens):
                    excerpt_lines.append(line)
                    if len("\n".join(excerpt_lines)) > 300:
                        break
            excerpt = "\n".join(excerpt_lines)[:300]
            section = md_file.parent.name
            results.append(KBResult(
                path=str(md_file.relative_to(KB_ROOT.parent)),
                score=score,
                excerpt=excerpt,
                section=section,
            ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]


def update_index() -> None:
    """Regenerate knowledge-base/README.md index from current files."""
    sections: dict[str, List[Path]] = {}
    for md_file in KB_ROOT.rglob("*.md"):
        if md_file.name == "README.md":
            continue
        sec = md_file.parent.name
        sections.setdefault(sec, []).append(md_file)

    lines = ["# 知识库索引\n"]
    for sec, files in sorted(sections.items()):
        lines.append(f"## {sec}\n")
        for f in sorted(files):
            rel = f.relative_to(KB_ROOT)
            lines.append(f"- [{f.stem}](./{rel})")
        lines.append("")

    from datetime import date
    lines.append(f"---\n\n**最后更新**：{date.today()}\n**维护者**：Writer Agent\n")
    (KB_ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Go error handling"
    for r in query(q):
        print(f"[{r.score:.2f}] {r.path} ({r.section})")
        print(r.excerpt)
        print()
