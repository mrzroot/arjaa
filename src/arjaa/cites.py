"""In-text citations and reference-list entries (author–year and numeric). Heuristic by design; see README «Limits»."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .docxio import Paragraph
from .norm import norm, key, is_persian

YEAR = r"(?<!\d)(1[34]\d\d|19\d\d|20\d\d)(?!\d)"
YEAR_RE = re.compile(YEAR)
SUFFIX = r"(?:[a-z]|[آ-ی])?"
STOP_NAMES = {"سال", "در", "از", "تا", "حدود", "حدودا", "year", "since", "in", "about", "around", "من", "ساعت", "مثلا", "مانند", "بین"}
SEE = r"(?:see|cf\.?|e\.g\.,?|i\.e\.,?|مثلاً|نک\.?|ر\.ک\.?|رک\.?|به\s+نقل\s+از)\s+"
ET_AL = re.compile(r"\s+(?:و\s*همکاران|et\s+al\.?|و\s+دیگران|و\s+ديگران)\s*$", re.I)


@dataclass
class Entry:
    para: int
    text: str
    number: Optional[int]          # numeric marker or implicit list number
    head: str                      # text up to the year (author area)
    tokens: frozenset
    year: Optional[int]
    year_in_parens: bool
    persian: bool
    cited: int = 0


@dataclass
class Cite:
    para: int
    kind: str                      # "paren" | "narr" | "num"
    raw: str
    surname: str = ""              # as typed
    tokens: Tuple[str, ...] = ()
    year: Optional[int] = None
    number: Optional[int] = None
    et_al: Optional[str] = None    # "fa" (و همکاران) | "en" (et al.) | None
    start: int = 0
    end: int = 0


def _tokens(s: str) -> frozenset:
    return frozenset(t for t in re.split(r"[^\w]+", key(s)) if len(t) > 1 or (t and not t.isascii()))


def parse_entry(p: Paragraph, implicit: Optional[int] = None) -> Entry:
    t = p.text.strip()
    n = norm(t)
    num = None
    m = re.match(r"^[\[\(]?(\d{1,3})[\]\)\.]\s*", n)
    if m:
        num = int(m.group(1))
        t_body, n_body = t[m.end():], n[m.end():]
    else:
        t_body, n_body = t, n
        num = implicit
    ym = re.search(r"\(\s*" + YEAR + SUFFIX + r"\s*\)", n_body)
    in_par = ym is not None
    if ym is None:
        ym = YEAR_RE.search(n_body)
    year = int(ym.group(1)) if ym else None
    head_end = ym.start() if ym else min(len(t_body), 70)
    head = t_body[:head_end]
    # the first author: up to the first « ، , ( & and و »
    first = re.split(r"[،,(]|\s&\s|\sand\s|\sو\s|\(", head, maxsplit=1)[0]
    toks = _tokens(first) or _tokens(head)
    # when the first author is written «Smith J.» keep every token; matching uses «cited ⊆ tokens»
    return Entry(p.idx, t, num, head.strip(), toks, year, in_par, is_persian(t_body[:60]))


def _first_author(name: str) -> Tuple[str, Optional[str]]:
    name = name.strip().strip("،,;؛ ")
    et = None
    m = ET_AL.search(name)
    if m:
        et = "fa" if "و" in m.group(0) else "en"
        name = name[:m.start()]
    name = re.split(r"\s+(?:&|and|و)\s+|[،,]", name, maxsplit=1)[0].strip()
    return name, et


def _seg_re():
    return re.compile(rf"^(?:{SEE})?(?P<name>[^\d;؛()\[\]]+?)\s*[،,]?\s*(?P<year>{YEAR}){SUFFIX}(?:\s*[،,:]\s*(?:pp?\.\s*|ص+\.?\s*)?\d+(?:\s*[-–]\s*\d+)?)?\s*$", re.I)


SEG = _seg_re()


def citations_in(p: Paragraph, known_heads: Optional[List[frozenset]] = None) -> List[Cite]:
    """Author–year citations in one paragraph: (Smith, 2020) · (رضایی و همکاران، ۱۳۹۸؛ Lee, 2019) · Smith (2020)."""
    t = norm(p.text)
    raw = p.text
    out: List[Cite] = []
    for m in re.finditer(r"\(([^()]*)\)", t):
        inner = m.group(1)
        if not YEAR_RE.search(inner):
            continue
        base = m.start(1)
        pos = 0
        for seg in re.split(r"[;؛]", inner):
            s0 = pos
            pos += len(seg) + 1
            mm = SEG.match(seg.strip())
            if mm:
                name_raw = raw[base + s0: base + s0 + len(seg)]
                nm = mm.group("name")
                if re.match(r"^\s*(?:" + "|".join(STOP_NAMES) + r")\b", nm, re.I) or len(nm.split()) > 7:
                    continue
                first, et = _first_author(nm)
                if not first:
                    continue
                out.append(Cite(p.idx, "paren", name_raw.strip(), first, tuple(sorted(_tokens(first))), int(mm.group("year")), None, et, base + s0, base + s0 + len(seg)))
                continue
            # narrative inside the bracket: «(Smith (2020))» is not handled
        # «Smith (2020)» — year alone in the brackets
        ym = re.match(rf"^\s*{YEAR}{SUFFIX}\s*(?:[،,:]\s*(?:pp?\.\s*|ص+\.?\s*)?\d+(?:\s*[-–]\s*\d+)?)?\s*$", inner)
        if ym:
            before = t[:m.start()].rstrip()
            mm = re.search(r"(\S+)\s+(?:و\s*همکاران|et\s+al\.?|و\s+دیگران)$", before, re.I)
            et = None
            if mm:
                name = mm.group(1)
                et = "fa" if "و" in before[mm.start(1) + len(name):] else "en"
            else:
                mm = re.search(r"(\S+)\s+(?:و|and|&)\s+(\S+)$", before)
                if mm:
                    name = mm.group(1)
                    if re.search(r"[\d()\[\]]", name):
                        name = mm.group(2)           # «… (1398) و رضایی (1400)»: the author is the word after «و»
                else:
                    mm = re.search(r"(\S+)$", before)
                    name = mm.group(1) if mm else ""
            name = name.strip("،,;؛:.()[]«»\"'“”")
            if not name or name.lower() in STOP_NAMES or name.isdigit():
                continue
            latin_cap = bool(re.match(r"^[A-Z][a-z'’\-]{2,}$", name))      # «Smith»; not «ResNet», «BERT», «LayerNorm»
            tk = _tokens(name)
            known = any(tk and tk <= h for h in (known_heads or []))
            if not (latin_cap or known):
                continue                     # a Persian word before «(۱۳۹۸)» is not provably an author
            out.append(Cite(p.idx, "narr", name + " (" + inner.strip() + ")",
                            name, tuple(sorted(tk)), int(YEAR_RE.search(inner).group(1)), None, et, m.start(), m.end()))
    return out


def numeric_cites(p: Paragraph) -> List[Cite]:
    t = norm(p.text)
    out: List[Cite] = []
    for m in re.finditer(r"\[\s*(\d{1,3}(?:\s*[-–,،]\s*\d{1,3})*)\s*\]", t):
        body = m.group(1)
        nums: List[int] = []
        parts = re.split(r"[,،]", body)
        for part in parts:
            r = re.match(r"^\s*(\d+)\s*[-–]\s*(\d+)\s*$", part)
            if r and 0 < int(r.group(2)) - int(r.group(1)) <= 60:
                nums.extend(range(int(r.group(1)), int(r.group(2)) + 1))
            else:
                nums.extend(int(x) for x in re.findall(r"\d+", part))
        for n in nums:
            out.append(Cite(p.idx, "num", m.group(0), number=n, start=m.start(), end=m.end()))
    return out


def sort_mode(entries: List[Entry], list_numbered: int) -> str:
    if not entries:
        return "none"
    explicit = sum(1 for e in entries if e.number is not None)
    return "numeric" if explicit >= 0.6 * len(entries) else "author-year"
