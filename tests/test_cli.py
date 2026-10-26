"""The demo documents and the command line: exit codes, --json, --strict, --map, odd inputs."""
import hashlib
import json
import os

from arjaa import cli, sample

from helpers import cap, codes, make, run


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


def test_exit_code_json_strict_combination(tmp_path):
    def b(d):
        d.heading("فصل دوم: الف", 1)
        cap(d, "شکل", 2, 1)
        d.p("شکل ۲-۹ را ببینید.")
    p = make(tmp_path, b)
    assert cli.main([p, "--json", "--skip", "A2"]) == 0      # prefix skip
    assert cli.main([p, "--json"]) == 1
