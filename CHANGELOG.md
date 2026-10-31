# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

Nothing user-facing yet, so no release was cut for these.

- Docs: README rewritten in English and Persian (banner, contents, before/after, features, limits, roadmap); CITATION.cff, issue forms and a pull-request template.
- Internal: unused imports and no-op code removed; the test file was split by subject with a shared `finding()` helper. No change in findings or output.

## [0.1.0] - 2026-10-24

First release.

### Added
- `arjaa FILE.docx`: check a Persian thesis for broken cross-references and citations. Figures and tables: duplicate numbers, gaps, a caption number whose chapter part does not match the chapter it sits in (`شکل ۲-۳` inside chapter 3), mentions of captions that do not exist, captions nobody mentions, mentions of chapters that do not exist (A1xx, A2xx).
- Citations against the reference list, author-year (APA-like, Persian and Latin mixed) and numeric `[n]`: citation without an entry, wrong year, entry never cited, duplicate entries, numbering gaps (A3xx).
- Persian-specific: `۱۳۹۸` / `1398` / `١٣٩٨` are the same year, ي/ك are folded, Latin entries with a Jalali year and Persian entries with a Gregorian year are flagged, `و همکاران` vs `et al.` against the language of the name.
- `--map` lists every caption with where it is mentioned and every reference entry with how often it is cited; `--json`, `--strict`, `--skip`, `--current-year`, `--demo`, `--make-sample`; `.txt`/`.md` input is supported. Reports only; never edits.
