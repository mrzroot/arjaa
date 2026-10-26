"""Shared helpers for the arjaa tests: build small .docx files and run the checks on them."""
from arjaa import checks
from arjaa.docxbuild import Doc
from arjaa.docxio import load


def codes(findings):
    """The set of finding codes in a list of findings."""
    return {f.code for f in findings}


def run(path, **kw):
    """Check the .docx at *path* with ``Options(**kw)``; returns ``(findings, info)``."""
    return checks.analyse(load(str(path)), checks.Options(**kw))


def make(tmp_path, build, name="t.docx"):
    """Create a .docx under *tmp_path*: ``build(doc)`` fills a fresh ``Doc``; returns the path."""
    d = Doc()
    build(d)
    return d.save(str(tmp_path / name))


def cap(d, label, ch, n, title="عنوان", seq="Figure"):
    """Add a caption «label ch-n: title» whose number is a live SEQ field, as Word's Insert Caption makes it."""
    d.caption_seq(label, ch, n, title, seq=seq)


def typed(d, text):
    """Add a caption whose number was typed by hand (no SEQ field)."""
    d.p(text, style="Caption")
