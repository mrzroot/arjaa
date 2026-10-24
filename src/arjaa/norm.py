"""Small text helpers: digit sets, Arabic/Persian letters, comparison keys. Every mapping is 1:1 in length so offsets survive."""
from __future__ import annotations

import re

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_TO_ASCII = str.maketrans(FA_DIGITS + AR_DIGITS, "0123456789" * 2)
_LETTERS = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه"})
ZWNJ = "\u200c"


def ascii_digits(s: str) -> str:
    return s.translate(_TO_ASCII)


def fa_digits(s: str) -> str:
    return s.translate(str.maketrans("0123456789", FA_DIGITS))


def norm(s: str) -> str:
    """Same length as the input: all digit sets → ASCII, Arabic ي/ك → Persian ی/ک. Offsets still point into the original."""
    return s.translate(_TO_ASCII).translate(_LETTERS)


_DROP = re.compile(r"[\u200c\u200d\u200e\u200f\u0640\u064b-\u065f]")


def key(s: str) -> str:
    """Comparison key: normalised letters/digits, no half-spaces/tatweel/diacritics, casefolded, single spaces."""
    s = _DROP.sub("", norm(s)).casefold()
    return re.sub(r"\s+", " ", s).strip()


def alnum_key(s: str) -> str:
    return re.sub(r"[^\w]+", "", key(s))


def is_persian(s: str) -> bool:
    return any("\u0600" <= c <= "\u06ff" for c in s)


def show(s: str, n: int = 90) -> str:
    s = re.sub(r"\s+", " ", s).strip().replace(ZWNJ, "⸱")
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"
