import hashlib
import json
import os
import random


from arjaa import checks, cli, norm, structure
from arjaa.docxbuild import Doc
from arjaa.docxio import load
from arjaa import sample


def codes(findings):
    return {f.code for f in findings}


def run(path, **kw):
    return checks.analyse(load(str(path)), checks.Options(**kw))


def make(tmp_path, build, name="t.docx"):
    d = Doc()
    build(d)
    return d.save(str(tmp_path / name))


def cap(d, label, ch, n, title="عنوان", seq="Figure"):
    d.caption_seq(label, ch, n, title, seq=seq)


def typed(d, text):
    d.p(text, style="Caption")


# ---------------------------------------------------------------- norm
def test_norm_keeps_length_so_offsets_survive():
    rnd = random.Random(7)
    alphabet = "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩0123456789يكىیکابپ \u200cـ.،-"
    for _ in range(300):
        s = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 40)))
        assert len(norm.norm(s)) == len(s)


def test_digit_sets_and_letters_normalise_together():
    assert norm.ascii_digits("۱۲-٣٤") == "12-34"
    assert norm.key("كتـاب\u200cها  ۱") == norm.key("کتابها 1")
    assert norm.fa_digits("2-13") == "۲-۱۳"


# ---------------------------------------------------------------- captions and mentions
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
        cap(d, "شکل", 2, 1); cap(d, "شکل", 2, 1)
        d.p("شکل ۲-۱ را ببینید.")
    f, _ = run(make(tmp_path, b))
    assert "A101" in codes(f)


def test_gap_start_and_backwards(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        d.p("شکل ۲-۲ و ۲-۴ و ۲-۳ را ببینید.")
        typed(d, "شکل ۲-۲: الف"); typed(d, "شکل ۲-۴: ب"); typed(d, "شکل ۲-۳: ج")
    f, _ = run(make(tmp_path, b))
    a102 = [x for x in f if x.code == "A102"][0]
    notes = " | ".join(e["note"] for e in a102.examples)
    assert "starts at 2" in notes and "skips" in notes and "goes back" in notes
    assert "۲-۳" in notes                                          # Persian digits for Persian labels


def test_chapter_prefix_mismatch_and_unknown_chapters(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1); cap(d, "شکل", 2, 1)
        d.heading("فصل سوم: ب", 1); cap(d, "شکل", 2, 2)
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
        cap(d, "شکل", 2, 1); cap(d, "جدول", 2, 1, seq="Table")
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
        typed(d, "شکل ۲-۱: الف"); typed(d, "شکل ۲: ب")
        d.p("شکل ۲-۱ و شکل ۲")
    f, _ = run(make(tmp_path, b))
    assert "A104" in codes(f)


def test_chapter_mention_beyond_last_chapter(tmp_path):
    def b(d):
        d.heading("فصل اول: الف", 1); d.heading("فصل دوم: ب", 1)
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
        d.heading("فصل دوم: الف", 1); cap(d, "شکل", 2, 1)
        d.p("در شکل ٢-١ آمده است.")
    f, _ = run(make(tmp_path, b))
    assert "A201" not in codes(f) and "A202" not in codes(f)


def test_toc_and_references_are_not_scanned_for_mentions(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1); cap(d, "شکل", 2, 1)
        d.p("شکل ۲-۱ را ببینید.")
        d.heading("منابع", 1)
        d.p("Smith, J. (2020). See figure 9-9 and Table 4-4 for details. Journal of Things.")
    f, _ = run(make(tmp_path, b))
    assert "A201" not in codes(f)


# ---------------------------------------------------------------- citations
def refs_doc(tmp_path, body, refs, head="منابع", name="r.docx"):
    def b(d):
        d.heading("فصل اول: مقدمه", 1)
        for t in body:
            d.p(t)
        d.heading(head, 1)
        for r in refs:
            d.p(r)
        d.heading("Abstract", 1)
        d.p("An English abstract that must not be read as a reference entry.")
    return make(tmp_path, b, name)


R_FA = "رضایی، علی و کریمی، سارا (۱۳۹۸). خوشه‌بندی داده‌های حسگر. مجله‌ی پژوهش‌های داده، ۱۲(۳)، ۴۵–۶۰."
R_EN = "Smith, J., & Lee, K. (2020). Clustering streaming sensor data. Journal of Sensor Studies, 10(2), 100–115."


def test_author_year_matching_both_ways(tmp_path):
    p = refs_doc(tmp_path, ["این روش (رضایی و کریمی، ۱۳۹۸) و (Smith & Lee, 2020) و Smith et al. (2020) آمده است."], [R_FA, R_EN])
    f, info = run(p)
    assert not (codes(f) & {"A321", "A322", "A323"})
    assert info["reference_list"]["entries"] == 2 and info["citations"] == 3 and info["reference_list"]["style"] == "author-year"


def test_citation_without_entry_year_mismatch_and_unused_entry(tmp_path):
    p = refs_doc(tmp_path, ["(Smith, 2021) و (Brown, 2018) و (رضایی، ۱۳۹۸)."], [R_FA, R_EN, "Wang, L. (2019). Survey of things. Journal of Stuff, 7(1), 5–40."])
    f, _ = run(p)
    d = {x.code: x for x in f}
    assert d["A322"].count == 1 and "2020" in d["A322"].examples[0]["note"]       # Smith 2021 vs 2020
    assert d["A321"].count == 1                                                    # Brown missing
    assert d["A323"].count == 1 and "Wang" in d["A323"].examples[0]["before"]      # Wang never cited
    assert "Smith" not in " ".join(e["before"] for e in d["A323"].examples)        # a wrong-year cite still counts as cited


def test_semicolon_groups_pages_and_prefixes(tmp_path):
    p = refs_doc(tmp_path, ["(رضایی و کریمی، ۱۳۹۸، ص ۴۵؛ Smith & Lee, 2020, pp. 100-110؛ see Smith, 2020)."], [R_FA, R_EN])
    f, info = run(p)
    assert info["citations"] == 3 and "A321" not in codes(f) and "A322" not in codes(f)


def test_years_in_ordinary_parentheses_are_not_citations(tmp_path):
    p = refs_doc(tmp_path, ["داده‌ها در (سال ۱۳۹۸) و (از ۱۳۹۰ تا ۱۳۹۵) و (۱۳۹۸) جمع شد و در سال (۲۰۱۹) هم."], [R_FA, R_EN])
    f, info = run(p)
    assert info["citations"] == 0


def test_persian_narrative_needs_a_known_author(tmp_path):
    p = refs_doc(tmp_path, ["حسگرها (۱۳۹۸) و رضایی (۱۴۰۰) و ایستگاه (۲۰۱۹) آمده‌اند."], [R_FA, R_EN])
    f, info = run(p)
    d = {x.code: x for x in f}
    assert info["citations"] == 1                      # only «رضایی (۱۴۰۰)»: a listed author, wrong year
    assert d["A322"].count == 1


def test_numeric_style(tmp_path):
    refs = ["[1] A. Author, Title one, Journal, 2019.", "[2] B. Author, Title two, Journal, 2020.", "[3] C. Author, Title three, Journal, 2021."]
    p = refs_doc(tmp_path, ["نتایج [3] و [1, 2] و [5] و [1-2] آمده است."], refs)
    f, info = run(p)
    d = {x.code: x for x in f}
    assert info["reference_list"]["style"] == "numeric"
    assert d["A311"].count == 1 and "[5]" in d["A311"].examples[0]["before"]
    assert "A312" not in d and "A313" in d             # first use order 3,1,2 is not 1,2,3


def test_numeric_list_gaps_and_unused(tmp_path):
    refs = ["[1] A. Author, Title one, Journal, 2019.", "[3] B. Author, Title two, Journal, 2020.", "[3] C. Author, Title three, Journal, 2021."]
    p = refs_doc(tmp_path, ["نتایج [1] آمده است."], refs)
    f, _ = run(p)
    d = {x.code: x for x in f}
    assert d["A314"].count == 2 and d["A312"].count == 2


def test_year_calendar_rules(tmp_path):
    refs = [R_FA, "Miller, A. (1399). Outlier handling. Data Letters, 3(4), 20–31.", "کاظمی، حسین (2019). مقایسه‌ی روش‌ها. پایان‌نامه.", "Zhou, Q. (2032). Drift. Preprint."]
    p = refs_doc(tmp_path, ["(رضایی و کریمی، ۱۳۹۸) و (Miller, 1399) و (کاظمی، 2019) و (Zhou, 2032)."], refs)
    f, _ = run(p, current_year=2026)
    c = codes(f)
    assert {"A331", "A332", "A333"} <= c
    f2, _ = run(p, current_year=2040)
    assert "A332" not in codes(f2)


def test_et_al_against_the_language_of_the_name(tmp_path):
    p = refs_doc(tmp_path, ["(رضایی et al., ۱۳۹۸) و (Smith و همکاران، 2020) و (Smith et al., 2020) و (رضایی و همکاران، ۱۳۹۸)."], [R_FA, R_EN])
    f, _ = run(p)
    a334 = [x for x in f if x.code == "A334"][0]
    assert a334.count == 2


def test_duplicate_entries(tmp_path):
    p = refs_doc(tmp_path, ["(Smith & Lee, 2020)."], [R_EN, R_EN.replace("Smith, J.", "Smith,  J.")])
    f, _ = run(p)
    assert "A341" in codes(f)


def test_reference_list_stops_before_the_english_abstract(tmp_path):
    p = refs_doc(tmp_path, ["(Smith & Lee, 2020)."], [R_EN])
    _, info = run(p)
    assert info["reference_list"]["entries"] == 1


def test_no_reference_list(tmp_path):
    def b(d):
        d.heading("فصل اول: مقدمه", 1)
        d.p("(Smith, 2020) و (Lee, 2019) و (Brown, 2018) آمده است.")
    f, _ = run(make(tmp_path, b))
    a301 = [x for x in f if x.code == "A301"][0]
    assert a301.severity == "warn"

    def b2(d):
        d.heading("فصل اول: مقدمه", 1)
        d.p("متن ساده.")
    f2, _ = run(make(tmp_path, b2, "n.docx"))
    assert [x for x in f2 if x.code == "A301"][0].severity == "info"


def test_reference_heading_variants(tmp_path):
    for head in ("فهرست منابع", "مراجع", "منابع و مآخذ", "References", "کتابنامه", "منابع:"):
        p = refs_doc(tmp_path, ["(Smith & Lee, 2020)."], [R_EN], head=head, name="h.docx")
        _, info = run(p)
        assert info["reference_list"]["found"], head


# ---------------------------------------------------------------- the demo and the CLI
def test_demo_flawed_finds_each_planted_problem(tmp_path):
    f, info = run(sample.thesis(str(tmp_path / "d.docx"), flawed=True), current_year=2026)
    want = {"A101", "A102", "A103", "A105", "A201", "A202", "A203", "A204", "A210", "A321", "A322", "A323", "A331", "A332", "A333", "A341"}
    assert want <= codes(f)
    assert info["reference_list"]["entries"] == 9


def test_demo_clean_is_silent(tmp_path):
    f, _ = run(sample.thesis(str(tmp_path / "c.docx"), flawed=False), current_year=2026)
    assert f == []


def test_cli_exit_codes_and_input_untouched(tmp_path, capsys):
    p = sample.thesis(str(tmp_path / "d.docx"), flawed=True)
    before = hashlib.sha256(open(p, "rb").read()).hexdigest()
    assert cli.main([p, "--no-color"]) == 1
    assert hashlib.sha256(open(p, "rb").read()).hexdigest() == before
    clean = sample.thesis(str(tmp_path / "c.docx"), flawed=False)
    assert cli.main([clean, "--no-color"]) == 0
    assert cli.main([str(tmp_path / "missing.docx")]) == 2
    bad = tmp_path / "x.pdf"
    bad.write_bytes(b"%PDF")
    assert cli.main([str(bad)]) == 2


def test_cli_strict_turns_warnings_into_failure(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)                    # never mentioned → warning only
    p = make(tmp_path, b)
    assert cli.main([p]) == 0
    assert cli.main([p, "--strict"]) == 1
    assert cli.main([p, "--strict", "--skip", "A202,A204"]) == 0


def test_cli_json_is_valid_and_complete(tmp_path, capsys):
    p = sample.thesis(str(tmp_path / "d.docx"), flawed=True)
    cli.main([p, "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["tool"] == "arjaa" and out["summary"]["errors"] >= 4
    assert out["map"]["captions"][0]["label"] == "شکل" and out["map"]["reference_entries"]
    assert all({"code", "severity", "title", "why", "fix"} <= set(x) for x in out["findings"])


def test_cli_map_and_demo(capsys):
    assert cli.main(["--demo", "--map", "--no-color"]) == 1
    out = capsys.readouterr().out
    assert "map: every caption" in out and "cited 0×" in out


def test_markdown_input(tmp_path, capsys):
    md = tmp_path / "t.md"
    md.write_text("# فصل دوم: الف\n\nدر شکل ۲-۳ آمده است. (Smith, 2020)\n\nشکل ۲-۱: پراکندگی\n\n# منابع\n\nSmith, J. (2019). A long title about things. Journal of Things.\n", encoding="utf-8")
    f, info = run(md)
    c = codes(f)
    assert "A201" in c and "A322" in c


def test_make_sample_writes_both_versions(tmp_path, capsys):
    assert cli.main(["--make-sample", str(tmp_path / "s.docx")]) == 0
    assert cli.main(["--make-sample", str(tmp_path / "s2.docx"), "--clean"]) == 0
    assert os.path.getsize(tmp_path / "s.docx") > 5000


def test_empty_and_corrupt_inputs(tmp_path):
    p = make(tmp_path, lambda d: None, "empty.docx")
    f, info = run(p)
    assert isinstance(f, list) and info["mentions"] == 0
    junk = tmp_path / "junk.docx"
    junk.write_bytes(b"not a zip at all")
    assert cli.main([str(junk)]) == 2


def test_table_cells_are_searched_for_mentions(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        d.table([["توضیح", "مرجع"], ["پراکندگی", "شکل ۲-۱"]])
    f, _ = run(make(tmp_path, b))
    assert "A202" not in codes(f)


def test_exit_code_json_strict_combination(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        d.p("شکل ۲-۹ را ببینید.")
    p = make(tmp_path, b)
    assert cli.main([p, "--json", "--skip", "A2"]) == 0      # prefix skip
    assert cli.main([p, "--json"]) == 1


def test_latin_model_names_with_numbers_are_not_citations(tmp_path):
    p = refs_doc(tmp_path, ["لایه LayerNorm (2048) و ResNet (2015) و BERT (2018) و Smith (2020) آمده است."], [R_EN])
    f, info = run(p)
    assert info["citations"] == 1 and "A332" not in codes(f)
