"""Reads the thesis skeleton: chapters, captions («شکل ۲-۳»), in-text mentions, the reference list."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .docxio import Document, Paragraph
from .norm import norm, key

ORD = {"اول": 1, "دوم": 2, "سوم": 3, "چهارم": 4, "پنجم": 5, "ششم": 6, "هفتم": 7, "هشتم": 8, "نهم": 9, "دهم": 10,
       "یازدهم": 11, "دوازدهم": 12, "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
       "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10}
LABELS = ("شکل", "جدول", "نمودار", "تصویر", "Figure", "Fig", "Table", "Chart")
LABEL_ALT = "شکل|جدول|نمودار|تصویر|Figure|Fig\\.?|Table|Chart"
CANON = {"fig": "Figure", "fig.": "Figure", "figure": "Figure", "table": "Table", "chart": "Chart"}
NUM = r"(\d+)(?:\s*[-–‐./]\s*(\d+))?"
CAP_RE = re.compile(rf"^\s*({LABEL_ALT})\s*{NUM}(?P<tail>.*)$", re.I | re.S)
MENTION_RE = re.compile(
    rf"(?<![\w])({LABEL_ALT})(?:[\u200c ]?(?:ها|های))?\s*(?P<list>{NUM}(?:\s*(?:،|,|و|تا|and|to)\s*{NUM})*)", re.I)
LEADER_RE = re.compile(r"(?:\t|\.{3,}|…|\s{3,})\s*[\d]+\s*$")
APPENDIX_RE = re.compile(r"^\s*(پیوست|ضمیمه|appendix|appendices)", re.I)
REF_HEAD_RE = re.compile(
    r"^(?:فصل\s+\S+\s*[:\-–]?\s*)?(?:\d+[\s.\-–)]*)?(منابع(?:\s+و\s+(?:مآخذ|مراجع))?|مراجع|فهرست\s+منابع(?:\s+و\s+مآخذ)?|کتابنامه|references?|bibliography|works\s+cited)\s*:?\s*$",
    re.I)
STOP_RE = re.compile(r"^\s*(پیوست|ضمیمه|واژه\s*نامه|واژه‌نامه|abstract|appendix|چکیده\s+انگلیسی|index)\b", re.I)


def canon_label(label: str) -> str:
    l = label.strip().rstrip(".")
    return CANON.get(l.lower(), l)


@dataclass
class Chapter:
    para: int
    number: int
    title: str
    explicit: bool


@dataclass
class Caption:
    para: int
    label: str
    chapter: Optional[int]       # None for single-number captions («شکل ۳»)
    n: int
    text: str
    has_seq: bool
    ref_ok: bool = True          # a bookmark around it? (not modelled) kept for future use

    @property
    def num(self) -> Tuple[Optional[int], int]:
        return (self.chapter, self.n)

    def label_text(self) -> str:
        return f"{self.label} {self.chapter}-{self.n}" if self.chapter is not None else f"{self.label} {self.n}"


@dataclass
class Mention:
    para: int
    label: str
    chapter: Optional[int]
    n: int
    start: int
    end: int


@dataclass
class Skeleton:
    chapters: List[Chapter] = field(default_factory=list)
    captions: List[Caption] = field(default_factory=list)
    mentions: List[Mention] = field(default_factory=list)
    chapter_mentions: List[Tuple[int, int, int, int]] = field(default_factory=list)   # para, n, start, end
    ref_head: Optional[int] = None
    ref_entries: List[Paragraph] = field(default_factory=list)
    ref_end: int = 0
    ref_fields: int = 0
    list_entries: int = 0
    chapter_at: List[Optional[int]] = field(default_factory=list)


def _heading_number(p: Paragraph) -> Tuple[Optional[int], bool]:
    t = norm(p.text).strip()
    m = re.match(r"^(?:فصل|chapter)\s+(\S+?)\s*[:\-–.،]?(?:\s|$)", t, re.I)
    if m:
        w = m.group(1).strip().lower()
        if w.isdigit():
            return int(w), True
        if w in ORD:
            return ORD[w], True
    m = re.match(r"^(\d{1,2})\s*[.\-–:)]?\s+\S", t)
    if m:
        return int(m.group(1)), True
    return None, False


def chapters_of(doc: Document) -> List[Chapter]:
    out: List[Chapter] = []
    auto = 0
    for p in doc.paragraphs:
        if p.heading_level != 1 or p.is_toc or not p.text.strip():
            continue
        n, explicit = _heading_number(p)
        if n is None and p.list_level is not None and not REF_HEAD_RE.match(key(p.text)) and not APPENDIX_RE.match(p.text):
            auto += 1
            n, explicit = auto, False
        elif n is not None:
            auto = n
        if n is not None:
            out.append(Chapter(p.idx, n, p.text.strip(), explicit))
    return out


def is_listing_line(p: Paragraph) -> bool:
    """A hand-made «فهرست اشکال» line: text, then dot leaders / a tab, then a page number."""
    return bool(LEADER_RE.search(p.text))


def caption_of(p: Paragraph) -> Optional[Caption]:
    if p.is_toc or p.heading_level or is_listing_line(p) or not p.text.strip():
        return None
    t = norm(p.text)
    m = CAP_RE.match(t)
    if not m:
        return None
    label = canon_label(m.group(1))
    a, b = m.group(2), m.group(3)
    tail = m.group("tail")
    style = (p.style_name or "").lower()
    has_seq = any(f.strip().upper().startswith("SEQ") for f in p.fields)
    caption_style = "caption" in style or "عنوان" in style and ("شکل" in style or "جدول" in style or "تصویر" in style)
    sep_ok = bool(re.match(r"^\s*[:：]", tail) or re.match(r"^\s+[-–—]\s+\S", tail) or re.match(r"^\s*\.\s+\S", tail) or re.match(r"^\s*[)\]]\s*\S", tail))
    if not (caption_style or has_seq or sep_ok):
        return None
    if b is None:
        return Caption(p.idx, label, None, int(a), p.text.strip(), has_seq)
    return Caption(p.idx, label, int(a), int(b), p.text.strip(), has_seq)


def mentions_in(p: Paragraph) -> List[Mention]:
    t = norm(p.text)
    out: List[Mention] = []
    for m in MENTION_RE.finditer(t):
        label = canon_label(m.group(1))
        lst = m.group("list")
        base = m.start("list")
        items = [(mm.group(1), mm.group(2), base + mm.start(), base + mm.end()) for mm in re.finditer(NUM, lst)]
        # expand «۲-۱ تا ۲-۳» when both ends share a chapter
        expanded: List[Tuple[Optional[int], int, int, int]] = []
        for i, (a, b, s, e) in enumerate(items):
            ch, n = (None, int(a)) if b is None else (int(a), int(b))
            if i > 0 and re.search(r"\bتا\b|\bto\b", lst[items[i - 1][3] - base:s - base]):
                pch, pn = expanded[-1][0], expanded[-1][1]
                if pch == ch and pn < n and n - pn <= 30:
                    for k in range(pn + 1, n):
                        expanded.append((ch, k, s, e))
            expanded.append((ch, n, s, e))
        for ch, n, s, e in expanded:
            out.append(Mention(p.idx, label, ch, n, s, e))
    return out


def chapter_mentions_in(p: Paragraph) -> List[Tuple[int, int, int, int]]:
    t = norm(p.text)
    out = []
    for m in re.finditer(r"(?<![\w])فصل\s+(?:‌?های\s+)?(\d{1,2})(?![\d.\-–/])", t):
        out.append((p.idx, int(m.group(1)), m.start(), m.end()))
    for m in re.finditer(r"(?<![\w])فصل\s+(" + "|".join(k for k in ORD if re.match(r"[آ-ی]", k)) + r")(?![\w])", t):
        out.append((p.idx, ORD[m.group(1)], m.start(), m.end()))
    return out


def find_reference_list(doc: Document) -> Tuple[Optional[int], List[Paragraph], int]:
    P = doc.paragraphs
    cand = [p for p in P if not p.is_toc and not p.in_table and len(p.text.strip()) <= 40 and REF_HEAD_RE.match(key(p.text))]
    if not cand:
        return None, [], 0
    # a heading style wins; otherwise the last candidate that has material after it
    heads = [p for p in cand if p.heading_level]
    head = (heads or cand)[-1]
    entries: List[Paragraph] = []
    end = head.idx
    for p in P[head.idx + 1:]:
        if p.in_table:
            continue
        if p.heading_level and p.heading_level <= (head.heading_level or 9) and p.text.strip():
            break
        if STOP_RE.match(key(p.text)) and len(p.text.strip()) <= 40:
            break
        end = p.idx
        if len(p.text.strip()) >= 12:
            entries.append(p)
    return head.idx, entries, end


def skeleton(doc: Document) -> Skeleton:
    sk = Skeleton()
    sk.chapters = chapters_of(doc)
    sk.ref_head, sk.ref_entries, sk.ref_end = find_reference_list(doc)
    for p in doc.paragraphs:
        if p.is_toc or (sk.ref_head is not None and sk.ref_head <= p.idx <= sk.ref_end):
            continue
        for f in p.fields:
            if re.match(r"^\s*(REF|PAGEREF)\s+_Ref", f, re.I):
                sk.ref_fields += 1
        if is_listing_line(p):
            sk.list_entries += 1
            continue
        c = caption_of(p)
        if c:
            sk.captions.append(c)
            continue
        if p.heading_level:
            continue
        sk.mentions.extend(mentions_in(p))
        sk.chapter_mentions.extend(chapter_mentions_in(p))
    sk.chapter_at = chapter_map(sk, doc)
    return sk


def chapter_map(sk: Skeleton, doc: Document) -> List[Optional[int]]:
    """Chapter number in force at each paragraph (None before the first chapter and inside appendices)."""
    starts = {c.para: c.number for c in sk.chapters}
    cur: Optional[int] = None
    out: List[Optional[int]] = []
    for p in doc.paragraphs:
        if p.idx in starts:
            cur = starts[p.idx]
        elif p.heading_level == 1 and APPENDIX_RE.match(p.text.strip()):
            cur = None
        out.append(cur)
    return out
