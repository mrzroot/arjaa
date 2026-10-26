"""Figure/table captions (A1xx) and mentions of them in the text (A2xx): numbering, chapter prefixes, dangling refs."""
from arjaa import sample, structure
from arjaa.docxio import load

from helpers import cap, codes, make, run, typed


def test_sentence_starting_with_label_is_not_a_caption(tmp_path):
    def b(d):
        d.heading("فصل دوم: مبانی", 1)
        d.p("شکل ۲-۱ نشان می‌دهد که روش جدید بهتر است.")
    doc = load(make(tmp_path, b))
    assert structure.skeleton(doc).captions == []


def test_caption_kinds_are_recognised(tmp_path):
    def b(d):
        d.heading("فصل دوم: مبانی", 1)
        typed(d, "شکل ۲-۱: الف")
        d.p("جدول ۲-۱ - ب")                      # spaced dash
        d.p("نمودار ۲-۱. ج")                      # dot + space
        cap(d, "شکل", 2, 2)                       # SEQ
    sk = structure.skeleton(load(make(tmp_path, b)))
    assert [(c.label, c.chapter, c.n) for c in sk.captions] == [("شکل", 2, 1), ("جدول", 2, 1), ("نمودار", 2, 1), ("شکل", 2, 2)]


def test_hand_made_list_of_figures_is_not_counted_twice(tmp_path):
    def b(d):
        d.heading("فهرست اشکال", 1)
        d.p("شکل ۲-۱: پراکندگی ........ ۱۲")
        d.p("شکل ۲-۲: خطا\t۱۴")
        d.heading("فصل دوم: مبانی", 1)
        d.p("در شکل ۲-۱ و شکل ۲-۲ دیده می‌شود.")
        cap(d, "شکل", 2, 1)
        cap(d, "شکل", 2, 2)
    f, info = run(make(tmp_path, b))
    assert "A101" not in codes(f) and "A202" not in codes(f)


def test_mentions_lists_ranges_plurals_and_digit_sets(tmp_path):
    def b(d):
        d.p("شکل‌های ۲-۱ و ۲-۲ و جدول ٢-٣ را ببینید؛ شکل ۲-۱ تا ۲-۴ و Fig. 3-1.")
    ms = structure.skeleton(load(make(tmp_path, b))).mentions
    got = {(m.label, m.chapter, m.n) for m in ms}
    assert ("شکل", 2, 1) in got and ("شکل", 2, 2) in got and ("جدول", 2, 3) in got
    assert ("شکل", 2, 3) in got and ("شکل", 2, 4) in got          # expanded range
    assert ("Figure", 3, 1) in got


def test_duplicate_caption_number(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        cap(d, "شکل", 2, 1)
        d.p("شکل ۲-۱ را ببینید.")
    f, _ = run(make(tmp_path, b))
    assert "A101" in codes(f)


def test_gap_start_and_backwards(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        d.p("شکل ۲-۲ و ۲-۴ و ۲-۳ را ببینید.")
        typed(d, "شکل ۲-۲: الف")
        typed(d, "شکل ۲-۴: ب")
        typed(d, "شکل ۲-۳: ج")
    f, _ = run(make(tmp_path, b))
    a102 = [x for x in f if x.code == "A102"][0]
    notes = " | ".join(e["note"] for e in a102.examples)
    assert "starts at 2" in notes and "skips" in notes and "goes back" in notes
    assert "۲-۳" in notes                                          # Persian digits for Persian labels


def test_chapter_prefix_mismatch_and_unknown_chapters(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        d.heading("فصل سوم: ب", 1)
        cap(d, "شکل", 2, 2)
        d.p("شکل ۲-۱ و ۲-۲")
    f, _ = run(make(tmp_path, b))
    assert "A103" in codes(f)

    def b2(d):                                                      # no chapter headings at all → note, no A103
        cap(d, "شکل", 2, 1)
        d.p("شکل ۲-۱")
    f2, _ = run(make(tmp_path, b2, "u.docx"))
    assert "A001" in codes(f2) and "A103" not in codes(f2)


def test_dangling_unreferenced_and_label_mismatch(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        cap(d, "جدول", 2, 1, seq="Table")
        d.p("در شکل ۲-۳ و نمودار ۲-۱ و جدول ۲-۱ دیده می‌شود.")
    f, _ = run(make(tmp_path, b))
    c = codes(f)
    assert {"A201", "A202", "A203"} <= c
    a201 = [x for x in f if x.code == "A201"][0]
    assert a201.count == 1 and "۲-۱" in a201.examples[0]["note"]
    a202 = [x for x in f if x.code == "A202"][0]
    assert a202.count == 1                                          # only the figure; the table is mentioned


def test_single_number_mention_against_chapter_captions_gets_a_hint(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        d.p("شکل ۱ را ببینید.")
    f, _ = run(make(tmp_path, b))
    a201 = [x for x in f if x.code == "A201"][0]
    assert "one number" in a201.examples[0]["note"]


def test_mixed_numbering_schemes(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        typed(d, "شکل ۲-۱: الف")
        typed(d, "شکل ۲: ب")
        d.p("شکل ۲-۱ و شکل ۲")
    f, _ = run(make(tmp_path, b))
    assert "A104" in codes(f)


def test_chapter_mention_beyond_last_chapter(tmp_path):
    def b(d):
        d.heading("فصل اول: الف", 1)
        d.heading("فصل دوم: ب", 1)
        d.p("نتایج در فصل ۷ و فصل دوم و فصل ۱ می‌آید و فصل سیزدهم نه.")
    f, _ = run(make(tmp_path, b))
    a210 = [x for x in f if x.code == "A210"][0]
    assert a210.count == 1


def test_typed_mentions_note_and_live_fields_silence_it(tmp_path):
    f, _ = run(sample.thesis(str(tmp_path / "x.docx"), flawed=True))
    assert "A204" in codes(f)
    f2, info2 = run(sample.thesis(str(tmp_path / "y.docx"), flawed=False))
    assert "A204" not in codes(f2) and info2["cross_reference_fields"] >= 5


def test_arabic_indic_digits_in_a_mention_still_match(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        d.p("در شکل ٢-١ آمده است.")
    f, _ = run(make(tmp_path, b))
    assert "A201" not in codes(f) and "A202" not in codes(f)


def test_toc_and_references_are_not_scanned_for_mentions(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        d.p("شکل ۲-۱ را ببینید.")
        d.heading("منابع", 1)
        d.p("Smith, J. (2020). See figure 9-9 and Table 4-4 for details. Journal of Things.")
    f, _ = run(make(tmp_path, b))
    assert "A201" not in codes(f)


def test_table_cells_are_searched_for_mentions(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        d.table([["توضیح", "مرجع"], ["پراکندگی", "شکل ۲-۱"]])
    f, _ = run(make(tmp_path, b))
    assert "A202" not in codes(f)
