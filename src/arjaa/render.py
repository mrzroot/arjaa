from __future__ import annotations

import json
import os
from typing import Dict, List

from . import __version__
from .checks import Finding, summary
from .norm import fa_digits

C = {"error": "\x1b[31m", "warn": "\x1b[33m", "info": "\x1b[34m", "dim": "\x1b[2m", "0": "\x1b[0m"}
SIGN = {"error": "✗", "warn": "!", "info": "·"}


def iso(s: str) -> str:
    """Fence quoted Persian samples with LRI…PDI so terminals keep the line layout stable."""
    return "\u2066" + s + "\u2069"


def _paras(f: Finding) -> str:
    ps = f.paragraphs
    tag = "  ".join(f"¶{p}" for p in ps[:6]) + (" …" if len(ps) > 6 or f.count > len(ps) else "")
    n = f"{f.count}× " if f.count > 1 else ""
    return n + tag


def text(doc, findings: List[Finding], info: Dict[str, object], color: bool = False, show_map: bool = False) -> str:
    def c(k, s):
        return f"{C[k]}{s}{C['0']}" if color else s
    sm = summary(doc, findings, info)
    out = [f"arjaa {__version__} · {os.path.basename(doc.path)} · {sm['paragraphs']} paragraphs"]
    caps = ", ".join(f"{n} «{l}»" for l, n in sm["captions"].items()) or "no captions found"
    ch = f"{sm['chapters']} chapters" if sm["chapters"] else "chapters not recognised"
    out.append(c("dim", f"floats: {caps} · {sm['mentions']} mention(s), {sm['cross_reference_fields']} Word cross-reference field(s) · {ch}"))
    rl = sm["reference_list"]
    if rl["found"]:
        out.append(c("dim", f"references: {rl['entries']} entries ({rl['style']}) · {sm['citations']} citation(s) recognised in the text"))
    else:
        out.append(c("dim", f"references: no list found · {sm['citations']} citation(s) recognised"))
    out.append("")
    if not findings:
        out.append("✓ nothing found by these rules.")
    for f in findings:
        out.append(f"{c(f.severity, SIGN[f.severity])} {f.code} {f.title}   [{_paras(f)}]")
        for e in f.examples:
            line = f"    {e['where']:>5}  {iso(e['before'])}"
            if e.get("note"):
                line += "   — " + e["note"]
            out.append(line)
        out.append(f"    why : {f.why}")
        out.append(f"    fix : {f.fix}")
        out.append("")
    out.append(f"{sm['errors']} error(s), {sm['warnings']} warning(s), {sm['info']} note(s). arjaa reports; it never edits your file.")
    na = sm["not_analysed"]
    if na:
        out.append("not analysed: " + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in na.items()))
    out.append("Heuristics, not a university validator: mentions and citations are found by pattern. Footnotes, text boxes and Zotero/EndNote fields are not read.")
    if show_map:
        out.append("")
        out.append(map_text(info))
    return "\n".join(out) + "\n"


def map_text(info: Dict[str, object]) -> str:
    lines = ["map: every caption, where it is, and where the text mentions it"]
    for c in info["captions"]:
        m = c["mentioned_in"]
        lines.append(f"  {iso(c['label'] + ' ' + c['number']):<18} ¶{c['paragraph']:<4} " + ("SEQ " if c["seq_field"] else "typed") + "   mentioned " + (", ".join(f"¶{x}" for x in m[:6]) + (" …" if len(m) > 6 else "") if m else "never"))
    ents = info["_entries"]
    if ents:
        lines.append("references: entry → times cited")
        for e in ents:
            lines.append(f"  ¶{e.para + 1:<4} {iso((e.head or e.text)[:44]):<52} {(fa_digits(str(e.year)) if e.persian else e.year) if e.year else '—'}   cited {e.cited}×")
    return "\n".join(lines)


def as_json(doc, findings: List[Finding], info: Dict[str, object]) -> str:
    pub = {k: v for k, v in info.items() if not k.startswith("_")}
    pub["reference_entries"] = [{"paragraph": e.para + 1, "number": e.number, "year": e.year, "authors": e.head, "cited": e.cited} for e in info["_entries"]]
    return json.dumps({"tool": "arjaa", "version": __version__, "file": os.path.basename(doc.path),
                       "summary": summary(doc, findings, info), "map": pub, "findings": [f.to_dict() for f in findings]},
                      ensure_ascii=False, indent=2)
