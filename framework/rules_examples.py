"""Static excerpts for the synthetic Axiom/Legalese Rules as Code example.

These helpers read the checked-in synthetic sources and presentation fixture.
They do not execute an engine, derive legal meaning or create a real encoding.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AXIOM_SOURCE = REPO_ROOT / 'research' / 'rules-visualization' / 'axiom' / 'procurement.rulespec.yaml'
L4_SOURCE = REPO_ROOT / 'research' / 'rules-visualization' / 'l4' / 'procurement.l4'
FIXTURE = REPO_ROOT / 'regions' / 'mena' / 'data' / 'visualizations' / 'synthetic-procurement.json'


def _excerpt(path: Path, marker: str, lines: int) -> str:
    text = path.read_text(encoding='utf-8').splitlines()
    start = 0
    for index, line in enumerate(text):
        if marker in line:
            start = index
            break
    return '\n'.join(line.rstrip() for line in text[start:start + lines]).strip()


def code_excerpts() -> dict[str, str]:
    """Return short, exact excerpts from the committed synthetic sources."""
    return {
        'axiom': _excerpt(AXIOM_SOURCE, 'name: procurement_obligation', 13),
        'l4': _excerpt(L4_SOURCE, '`procurement outcome`', 18),
    }


def ladder_excerpt(limit: int = 3) -> list[dict]:
    """Return the first synthetic ladder steps from the checked-in fixture."""
    data = json.loads(FIXTURE.read_text(encoding='utf-8'))
    return (data.get('ladder') or [])[:limit]
