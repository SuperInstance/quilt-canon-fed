"""Canon lore loader — finds and parses canon_writings/*.md files."""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional


def _parse_simple_yaml(text: str) -> dict:
    """Tiny YAML-ish parser for our front matter (no PyYAML dep)."""
    if not text.strip():
        return {}
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        # Strip surrounding quotes
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        elif val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        # List value?
        if val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
            result[key] = items
        elif val.lower() in ("yes", "true"):
            result[key] = True
        elif val.lower() in ("no", "false"):
            result[key] = False
        else:
            result[key] = val
    return result


# 5 bedrock doctrines
DOCTRINES = [
    "cells_are_scars",
    "witness_log_is_prediction",
    "canon_gate_is_chord",
    "oracle_is_heard",
    "substrate_quantum",
]


class CanonPiece:
    """A single canon lore file."""

    def __init__(self, name: str, path: Path, body: str, meta: dict):
        self.name = name
        self.path = path
        self.body = body
        self.meta = meta or {}
        self.title = self.meta.get("title", name)
        self.tags = self.meta.get("tags", [])
        self.characters = self.meta.get("characters", [])
        self.doctrines_hit = self._detect_doctrines()
        self.composite = self.meta.get("composite", None)

    def _detect_doctrines(self) -> List[str]:
        text = (self.body + " " + self.title).lower()
        hit = []
        for d in DOCTRINES:
            # Match doctrine by keywords
            keywords = {
                "cells_are_scars": ["scar", "scars", "cell is", "cells are"],
                "witness_log_is_prediction": ["witness log", "witness-log", "log is a prediction"],
                "canon_gate_is_chord": ["chord", "canon gate", "consensus"],
                "oracle_is_heard": ["oracle", "heard", "jev"],
                "substrate_quantum": ["quantum", "substrate", "walker"],
            }
            for kw in keywords.get(d, [d]):
                if kw in text:
                    hit.append(d)
                    break
        return hit

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "tags": self.tags,
            "characters": self.characters,
            "doctrines_hit": self.doctrines_hit,
            "composite": self.composite,
            "body": self.body[:500] + ("..." if len(self.body) > 500 else ""),
            "path": str(self.path),
        }


def _split_frontmatter(text: str):
    """Split YAML front matter from body."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm = text[3:end].strip()
    body = text[end + 3:].strip()
    meta = _parse_simple_yaml(fm)
    return meta, body


def find_canon_dirs() -> List[Path]:
    """Find all directories that contain canon lore."""
    candidates = [
        Path("/workspace/research/canon_writings"),
        Path("/workspace/research/substrate-walker/canon/cells"),
    ]
    found = [d for d in candidates if d.exists()]
    return found


def load_canon(canon_dir: Optional[Path] = None) -> List[CanonPiece]:
    """Load all canon lore from a directory. Searches by default."""
    if canon_dir is None:
        dirs = find_canon_dirs()
    else:
        dirs = [canon_dir]
    pieces = []
    for d in dirs:
        for md in sorted(d.glob("*.md")):
            text = md.read_text(encoding="utf-8")
            meta, body = _split_frontmatter(text)
            name = md.stem
            pieces.append(CanonPiece(name, md, body, meta))
    return pieces


def get_by_name(name: str, canon_dir: Optional[Path] = None) -> Optional[CanonPiece]:
    """Get a single canon piece by name."""
    for p in load_canon(canon_dir):
        if p.name == name or p.title.lower() == name.lower():
            return p
    return None


def get_by_doctrine(doctrine: str, canon_dir: Optional[Path] = None) -> List[CanonPiece]:
    """Return canon pieces anchored to a doctrine."""
    return [p for p in load_canon(canon_dir) if doctrine in p.doctrines_hit]
