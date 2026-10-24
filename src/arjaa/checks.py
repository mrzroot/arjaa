"""arjaa checks: caption numbering, figure/table mentions, chapter mentions, citations vs the reference list."""
from __future__ import annotations

import datetime
import re
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple

from . import cites as ct
from . import structure as st
from .docxio import Document
from .norm import norm, key, alnum_key, is_persian, fa_digits, show

SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}
MAX_EX = 5


@dataclass
class Options:
    current_year: Optional[int] = None     # Gregorian; default: today
    skip: Tuple[str, ...] = ()             # finding codes (or prefixes such as «A3») to leave out


@dataclass
class Finding:
    code: str
    severity: str
    title: str
    why: str
    fix: str
    count: int = 0
    paragraphs: List[int] = field(default_factory=list)       # 1-based
    examples: List[Dict[str, str]] = field(default_factory=list)

    def add(self, para: Optional[int], before: str, note: str = "", example: bool = True) -> None:
        """para: 0-based paragraph index, or None for a finding about the whole document."""
        self.count += 1
        if para is not None and para + 1 not in self.paragraphs and len(self.paragraphs) < 40:
            self.paragraphs.append(para + 1)
        if example and len(self.examples) < MAX_EX:
            self.examples.append({"where": f"¶{para + 1}" if para is not None else "doc", "before": before, "note": note})

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v not in (None, [], "")}


META = {
    "A001": ("info", "chapter headings were not recognised", "Chapter-prefix checks (does «شکل ۲-۳» sit in chapter 2?) need to know where chapters start. arjaa looks for Heading 1 paragraphs like «فصل دوم», «فصل ۲», «۲ مقدمه», or automatically numbered Heading 1.", "Use the Heading 1 style for chapter titles (the check is skipped until then)."),
    "A101": ("error", "the same caption number is used twice", "Two figures (or tables) with one number make every in-text reference ambiguous.", "Renumber one of them; if the captions use Word's SEQ field, press Ctrl+A, F9."),
    "A102": ("warn", "caption numbers skip or go backwards", "A gap usually means a figure was deleted or moved and the numbers were typed by hand; a backwards step means one was pasted in from another chapter.", "Renumber (Insert → Caption does it automatically), then update every mention."),
    "A103": ("warn", "caption chapter prefix does not match the chapter it sits in", "«شکل ۲-۴» inside chapter 3 usually means the caption was copied from another chapter and not renumbered.", "Fix the typed chapter part; with SEQ captions, keep the chapter number in the label text up to date."),
    "A104": ("info", "captions of one kind use both «۲-۳» and «۳» numbering", "One thesis should number its figures one way (chapter-number, or running number).", "Choose one scheme for each caption type."),
    "A105": ("info", "captions typed by hand (no SEQ field)", "Typed numbers do not follow when a figure is inserted or removed; Word's Insert → Caption keeps them in step.", "Optional: re-insert the captions with Insert → Caption."),
    "A201": ("error", "mention of a figure/table that has no caption", "The text points at a number that does not exist in this document (typo, deleted figure, or a number from another chapter).", "Correct the mention or add the missing caption."),
    "A202": ("warn", "figure/table never mentioned in the text", "Most universities expect every figure and table to be introduced in the text before it appears.", "Add a sentence such as «نتایج در شکل ۲-۳ آمده است» or remove the figure."),
    "A203": ("info", "mentions use a caption label nobody uses", "The text says «نمودار ۲-۱» but the captions say «شکل …» (or the reverse), so the two cannot be matched.", "Use one word per kind of float in captions and in text."),
    "A204": ("info", "mentions are typed, not Word cross-references", "A mention typed by hand does not change when a caption is renumbered; Insert → Cross-reference keeps them in step.", "Optional: replace typed mentions with Insert → Cross-reference (then update fields before exporting)."),
    "A210": ("warn", "mention of a chapter that does not exist", "For example «در فصل ۷» in a thesis with five chapters.", "Correct the chapter number."),
    "A301": ("warn", "no reference list found", "arjaa looks for a heading such as «منابع», «مراجع», «فهرست منابع», «References».", "Name the list's heading in one of these ways (a Heading 1 is best)."),
    "A311": ("error", "[n] cited but there is no entry n", "The reference list is shorter than the numbers cited, or an entry was deleted.", "Add the entry or fix the number."),
    "A312": ("warn", "reference entry never cited", "A listed work that the text never cites.", "Cite it or remove it."),
    "A313": ("info", "numbers are not in order of first appearance", "Fine for an alphabetical list; a problem if your university asks for numbering in order of appearance.", "Renumber if your style needs it."),
    "A314": ("error", "reference numbers are not 1…n", "Duplicate, skipped, or out-of-order numbers in the list.", "Renumber the list."),
    "A321": ("error", "citation without a matching reference entry", "No entry has this author (and year) in the list.", "Add the entry, or correct the name."),
    "A322": ("error", "citation year differs from the reference entry", "The list has this author, but with another year: usually a typo, or one of two works by the same author.", "Make the year in the text and in the list agree."),
    "A323": ("warn", "reference entry never cited", "Listed in the references but not cited in the text (only parenthetical citations with a clear author and year, and narrative ones, are recognised).", "Cite it or remove it."),
    "A331": ("warn", "Latin-script entry with a Jalali-range year", "A year like 1399 on an English reference is almost always a typo or a pasted Persian entry.", "Check the year."),
    "A332": ("warn", "year in the future", "Citation or entry year is later than the current year (Gregorian) or Jalali year.", "Check the year."),
    "A333": ("info", "Persian-script entry with a Gregorian year", "Not wrong (some sources are dated that way), but mixed calendars confuse readers and in-text matching.", "Be consistent: Jalali for Persian sources, Gregorian for the others."),
    "A334": ("info", "«و همکاران» vs «et al.» used against the language of the name", "Persian names take «و همکاران», Latin names «et al.»; this one is the other way round.", "Use the form that matches the author's language."),
    "A341": ("warn", "duplicate or near-duplicate reference entries", "The same work listed twice (it will then be cited twice, under two numbers).", "Keep one entry."),
}


def mk(code: str) -> Finding:
    sev, title, why, fix = META[code]
    return Finding(code, sev, title, why, fix)


def _jalali_max(cur_g: int) -> int:
    return cur_g - 621 + 1


def analyse(doc: Document, opt: Optional[Options] = None) -> Tuple[List[Finding], Dict[str, object]]:
    opt = opt or Options()
    cur_g = opt.current_year or datetime.date.today().year
    F: Dict[str, Finding] = {}

    def f(code: str) -> Finding:
        if code not in F:
            F[code] = mk(code)
        return F[code]

    sk = st.skeleton(doc)
    P = doc.paragraphs
    cap_by_label: "OrderedDict[str, List[st.Caption]]" = OrderedDict()
    for c in sk.captions:
        cap_by_label.setdefault(c.label, []).append(c)

    # ------------------------------------------------------------ captions
    double_present = any(c.chapter is not None for c in sk.captions)
    if double_present and not sk.chapters:
        f("A001").add(None, "no Heading 1 paragraph looks like a numbered chapter", example=False)
    for label, caps in cap_by_label.items():
        seen: Dict[Tuple[Optional[int], int], st.Caption] = {}
        last: Dict[Optional[int], int] = {}
        for c in caps:
            if c.num in seen:
                f("A101").add(c.para, show(c.text), f"same number as ¶{seen[c.num].para + 1}")
            else:
                seen[c.num] = c
                prev = last.get(c.chapter, 0)
                if c.n > prev + 1:
                    miss = list(range(prev + 1, c.n))
                    ms = ", ".join(_num(c.chapter, k, label) for k in miss[:3]) + (" …" if len(miss) > 3 else "")
                    f("A102").add(c.para, show(c.text), f"skips {ms}" if prev else f"starts at {c.n}, not 1 (missing {ms})")
                elif c.n < prev:
                    f("A102").add(c.para, show(c.text), f"goes back (after {_num(c.chapter, prev, label)})")
                last[c.chapter] = max(prev, c.n)
            cur = sk.chapter_at[c.para] if sk.chapter_at else None
            if c.chapter is not None and cur is not None and c.chapter != cur:
                f("A103").add(c.para, show(c.text), f"sits in chapter {cur}")
        kinds = {c.chapter is None for c in caps}
        if len(kinds) == 2:
            single = [c for c in caps if c.chapter is None]
            f("A104").add(single[0].para, show(single[0].text), f"«{label}»: {len(single)} single-number, {len(caps) - len(single)} chapter-number captions")
    typed = [c for c in sk.captions if not c.has_seq]
    if typed:
        g = f("A105")
        for c in typed:
            g.add(c.para, show(c.text), "", example=g.count < 2)

    # ------------------------------------------------------------ mentions
    by_num: Dict[str, Dict[Tuple[Optional[int], int], st.Caption]] = {l: {c.num: c for c in cs} for l, cs in cap_by_label.items()}
    mentioned: Set[Tuple[str, Tuple[Optional[int], int]]] = set()
    mention_map: Dict[Tuple[str, Tuple[Optional[int], int]], List[int]] = defaultdict(list)
    orphan_labels: Dict[str, List[st.Mention]] = defaultdict(list)
    typed_mentions = 0
    for m in sk.mentions:
        typed_mentions += 1
        table = by_num.get(m.label)
        if table is None:
            orphan_labels[m.label].append(m)
            continue
        k = (m.chapter, m.n)
        if k in table:
            mentioned.add((m.label, k))
            mention_map[(m.label, k)].append(m.para)
        else:
            hint = ""
            if m.chapter is None and any(c is not None for c, _ in table):
                hint = "captions are numbered like «۲-۳», the mention has one number"
            elif m.chapter is not None and any(c is None for c, _ in table):
                hint = "captions have one running number, the mention has two"
            else:
                near = sorted(table, key=lambda x: (x[0] or 0, x[1]))
                hint = "captions: " + ", ".join(_num(c, n, m.label) for c, n in near[:6]) + (" …" if len(near) > 6 else "")
            f("A201").add(m.para, _ctx(P[m.para].text, m.start, m.end), hint)
    for label, caps in cap_by_label.items():
        for c in caps:
            if (label, c.num) not in mentioned:
                f("A202").add(c.para, show(c.text), "", example=True)
    # a duplicate caption is listed once
    if "A202" in F:
        seen_cap = set()
        keep = []
        for ex in F["A202"].examples:
            if ex["before"] not in seen_cap:
                seen_cap.add(ex["before"])
                keep.append(ex)
        F["A202"].examples = keep
    for label, ms in orphan_labels.items():
        others = ", ".join(f"«{l}»" for l in cap_by_label) or "none"
        f("A203").add(ms[0].para, _ctx(P[ms[0].para].text, ms[0].start, ms[0].end), f"{len(ms)}× «{label}»; captions use {others}")
    if sk.captions and typed_mentions:
        if sk.ref_fields == 0:
            f("A204").add(None, f"{typed_mentions} typed mention(s), 0 Word cross-reference fields", example=True)
        elif sk.ref_fields < typed_mentions:
            f("A204").add(None, f"{typed_mentions} typed mention(s), only {sk.ref_fields} Word cross-reference field(s)", example=True)

    # ------------------------------------------------------------ chapter mentions
    if len(sk.chapters) >= 2:
        top = max(c.number for c in sk.chapters)
        for para, n, a, b in sk.chapter_mentions:
            if n > top or n < 1:
                f("A210").add(para, _ctx(P[para].text, a, b), f"the thesis has {top} chapters")

    # ------------------------------------------------------------ citations
    entries: List[ct.Entry] = []
    implicit = 0
    for p in sk.ref_entries:
        implicit += 1
        entries.append(ct.parse_entry(p, implicit if p.list_level is not None else None))
    mode = ct.sort_mode(entries, 0)
    heads = [e.tokens for e in entries]
    cites: List[ct.Cite] = []
    ref_lo = sk.ref_head if sk.ref_head is not None else 10 ** 9
    for p in P:
        if p.is_toc or (sk.ref_head is not None and ref_lo <= p.idx <= sk.ref_end) or p.heading_level:
            continue
        if mode == "numeric":
            cites.extend(ct.numeric_cites(p))
        else:
            cites.extend(ct.citations_in(p, heads))
    jmax, gmax = _jalali_max(cur_g), cur_g + 1
    if sk.ref_head is None or not entries:
        n_cites = len(cites) or len(sum([ct.numeric_cites(p) for p in P if not p.is_toc], []))
        if n_cites >= 3:
            f("A301").add(None, f"{n_cites} citation(s) found, no list headed «منابع / مراجع / References»", example=True)
        else:
            F["A301"] = mk("A301")
            F["A301"].severity = "info"
            F["A301"].add(None, "no reference list found; citation checks skipped", example=True)
    elif mode == "numeric":
        _numeric(entries, cites, f, P)
    else:
        _author_year(entries, cites, f, P)
    # years and scripts (entries)
    for e in entries:
        if e.year is None:
            continue
        if not e.persian and 1300 <= e.year < 1500:
            f("A331").add(e.para, show(e.text), f"year {e.year}")
        if (e.year < 1900 and e.year > jmax) or (e.year >= 1900 and e.year > gmax):
            f("A332").add(e.para, show(e.text), f"year {e.year}")
        if e.persian and e.year >= 1900:
            f("A333").add(e.para, show(e.text), f"year {e.year}")
    for c in cites:
        if c.year and ((c.year < 1900 and c.year > jmax) or (c.year >= 1900 and c.year > gmax)):
            f("A332").add(c.para, _short(c), f"year {c.year}")
        if c.et_al == "en" and is_persian(c.surname):
            f("A334").add(c.para, _short(c), "Persian name + «et al.»")
        elif c.et_al == "fa" and c.surname and not is_persian(c.surname):
            f("A334").add(c.para, _short(c), "Latin name + «و همکاران»")
    # duplicates in the list
    seen: Dict[str, ct.Entry] = {}
    for e in entries:
        k1 = alnum_key(re.sub(r"^[\[\(]?\d{1,3}[\]\)\.]\s*", "", e.text))
        k2 = k1[:70]
        hit = seen.get(k2)
        if hit is not None and len(k2) >= 25:
            f("A341").add(e.para, show(e.text), f"same as ¶{hit.para + 1}")
        else:
            seen[k2] = e

    out = [x for x in F.values() if x.count and not any(x.code.startswith(s) for s in opt.skip)]
    out.sort(key=lambda x: (SEVERITY_ORDER[x.severity], x.code))
    info = {
        "chapters": [{"number": c.number, "title": show(c.title, 60)} for c in sk.chapters],
        "captions": [{"label": c.label, "number": _num(c.chapter, c.n, c.label), "paragraph": c.para + 1, "seq_field": c.has_seq,
                      "mentioned_in": [p + 1 for p in mention_map.get((c.label, c.num), [])]} for c in sk.captions],
        "mentions": len(sk.mentions),
        "cross_reference_fields": sk.ref_fields,
        "reference_list": {"found": sk.ref_head is not None, "paragraph": (sk.ref_head + 1) if sk.ref_head is not None else None,
                           "entries": len(entries), "style": mode},
        "citations": len(cites),
        "_entries": entries, "_cites": cites,
    }
    return out, info


def _num(ch: Optional[int], n: int, label: str = "") -> str:
    s = f"{ch}-{n}" if ch is not None else str(n)
    return fa_digits(s) if is_persian(label) else s


def _ctx(text: str, a: int, b: int, w: int = 24) -> str:
    return show(text[max(0, a - w):a] + "⟦" + text[a:b] + "⟧" + text[b:b + w], 120)


def _short(c: ct.Cite) -> str:
    return show(c.raw if c.kind != "num" else c.raw, 80)


def _match(c: ct.Cite, entries: List[ct.Entry]):
    ctk = frozenset(c.tokens)
    same_author = [e for e in entries if ctk and ctk <= e.tokens]
    exact = [e for e in same_author if e.year == c.year]
    return exact, same_author


def _author_year(entries, cites, f, P) -> None:
    for c in cites:
        exact, same = _match(c, entries)
        if exact:
            for e in exact:
                e.cited += 1
        elif same:
            yrs = sorted({e.year for e in same if e.year})
            f("A322").add(c.para, _short(c), f"list has {c.surname} with " + ", ".join(fa_digits(str(y)) if is_persian(c.surname) else str(y) for y in yrs))
            for e in same:
                e.cited += 1                 # the entry is cited (with a wrong year); do not also report it as unused
        else:
            f("A321").add(c.para, _short(c), "")
    for e in entries:
        if e.cited == 0:
            f("A323").add(e.para, show(e.text))


def _numeric(entries, cites, f, P) -> None:
    nums = [e.number for e in entries]
    have = {e.number: e for e in entries if e.number is not None}
    # numbering of the list itself
    prob: List[str] = []
    prev = 0
    for e in entries:
        if e.number is None:
            prob.append("no number")
            f("A314").add(e.para, show(e.text), "entry without a number")
            continue
        if e.number == prev:
            f("A314").add(e.para, show(e.text), f"number {e.number} repeated")
        elif e.number != prev + 1:
            f("A314").add(e.para, show(e.text), f"expected {prev + 1}, found {e.number}")
        prev = e.number
    first_order: List[int] = []
    for c in cites:
        if c.number not in have:
            f("A311").add(c.para, c.raw, f"the list has {len(entries)} entries" if entries else "")
        else:
            have[c.number].cited += 1
            if c.number not in first_order:
                first_order.append(c.number)
    for e in entries:
        if e.cited == 0 and e.number is not None:
            f("A312").add(e.para, show(e.text))
    if len(first_order) >= 3 and first_order != sorted(first_order):
        k = next(i for i in range(len(first_order) - 1) if first_order[i] > first_order[i + 1])
        f("A313").add(None, "first citations in order: " + ", ".join(f"[{x}]" for x in first_order[:8]) + (" …" if len(first_order) > 8 else ""),
                      f"[{first_order[k + 1]}] is first cited after [{first_order[k]}]")
    return None


def summary(doc: Document, findings: List[Finding], info: Dict[str, object]) -> Dict[str, object]:
    cnt = Counter(x.severity for x in findings)
    caps = Counter(c["label"] for c in info["captions"])
    return {
        "paragraphs": len(doc.paragraphs), "chapters": len(info["chapters"]), "captions": dict(caps),
        "mentions": info["mentions"], "cross_reference_fields": info["cross_reference_fields"],
        "reference_list": info["reference_list"], "citations": info["citations"],
        "errors": cnt["error"], "warnings": cnt["warn"], "info": cnt["info"],
        "not_analysed": {k: v for k, v in doc.unsupported.items() if v},
    }
