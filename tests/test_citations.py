"""Citations and the reference list (A3xx): author-year and numeric styles, years, duplicates, list boundaries."""
from helpers import codes, finding, make, run


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
    a334 = finding(f, "A334")
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
    a301 = finding(f, "A301")
    assert a301.severity == "warn"

    def b2(d):
        d.heading("فصل اول: مقدمه", 1)
        d.p("متن ساده.")
    f2, _ = run(make(tmp_path, b2, "n.docx"))
    assert finding(f2, "A301").severity == "info"


def test_reference_heading_variants(tmp_path):
    for head in ("فهرست منابع", "مراجع", "منابع و مآخذ", "References", "کتابنامه", "منابع:"):
        p = refs_doc(tmp_path, ["(Smith & Lee, 2020)."], [R_EN], head=head, name="h.docx")
        _, info = run(p)
        assert info["reference_list"]["found"], head


def test_latin_model_names_with_numbers_are_not_citations(tmp_path):
    p = refs_doc(tmp_path, ["لایه LayerNorm (2048) و ResNet (2015) و BERT (2018) و Smith (2020) آمده است."], [R_EN])
    f, info = run(p)
    assert info["citations"] == 1 and "A332" not in codes(f)
