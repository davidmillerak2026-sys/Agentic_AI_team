from __future__ import annotations

from pathlib import Path

from .models import EvidenceItem


SUPPORTED_SUFFIXES = {".md", ".txt", ".json", ".csv", ".yaml", ".yml"}


def load_evidence(paths: list[str] | tuple[str, ...] | None, *, max_chars: int = 4000) -> list[EvidenceItem]:
    if not paths:
        return []
    evidence: list[EvidenceItem] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in SUPPORTED_SUFFIXES:
                    evidence.append(_read_one(child, max_chars=max_chars))
        elif path.is_file():
            evidence.append(_read_one(path, max_chars=max_chars))
        else:
            evidence.append(
                EvidenceItem(
                    title=f"missing:{path.name}",
                    source=str(path),
                    text=f"Evidence path was not found: {path}",
                    score=0.0,
                )
            )
    return evidence


def _read_one(path: Path, *, max_chars: int) -> EvidenceItem:
    text = path.read_text(encoding="utf-8", errors="replace")
    return EvidenceItem(title=path.name, source=str(path), text=text[:max_chars], score=1.0)
