from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from . import __version__, checks, render
from .docxio import load


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="arjaa", description=(
        "Cross-reference and citation integrity check for a Persian thesis (.docx): figure/table numbers (شکل ۲-۳), "
        "mentions in the text, and in-text citations against the reference list. Offline; reports only, never edits."))
    ap.add_argument("file", nargs="?", help=".docx (or .txt/.md)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings too (default: only on errors)")
    ap.add_argument("--map", action="store_true", help="also print every caption with where it is mentioned, and every reference entry with how often it is cited")
    ap.add_argument("--skip", default="", help="comma-separated finding codes or prefixes to leave out, e.g. A105,A3")
    ap.add_argument("--current-year", type=int, help="Gregorian year used for the «year in the future» check (default: today)")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--demo", action="store_true", help="offline: generate a sample thesis chapter and check it")
    ap.add_argument("--make-sample", metavar="PATH", help="write the synthetic demo .docx to PATH and exit (with --clean: the clean version)")
    ap.add_argument("--clean", action="store_true", help="with --make-sample: write the clean version")
    ap.add_argument("--version", action="version", version=f"arjaa {__version__}")
    a = ap.parse_args(argv)
    rest = list(argv if argv is not None else sys.argv[1:])
    if a.demo:
        import tempfile
        from . import sample
        with tempfile.TemporaryDirectory() as td:
            path = sample.thesis(os.path.join(td, "thesis.docx"))
            return main([path] + [x for x in rest if x != "--demo"])
    if a.make_sample:
        from . import sample
        print(sample.thesis(a.make_sample, flawed=not a.clean))
        return 0
    if not a.file:
        ap.error("give a .docx file (or use --demo)")
    if not os.path.exists(a.file):
        print(f"arjaa: no such file: {a.file}", file=sys.stderr)
        return 2
    try:
        doc = load(a.file)
    except Exception as e:
        print(f"arjaa: cannot read {a.file}: {e}", file=sys.stderr)
        return 2
    skip = tuple(x.strip() for x in a.skip.split(",") if x.strip())
    findings, info = checks.analyse(doc, checks.Options(current_year=a.current_year, skip=skip))
    if a.json:
        sys.stdout.write(render.as_json(doc, findings, info) + "\n")
    else:
        sys.stdout.write(render.text(doc, findings, info, color=sys.stdout.isatty() and not a.no_color, show_map=a.map))
    bad = sum(1 for f in findings if f.severity == "error") + (sum(1 for f in findings if f.severity == "warn") if a.strict else 0)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
