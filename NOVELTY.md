# Novelty check: arjaa

Done 2026-10-24 before publishing. Wording is deliberately modest. **Checking citations against a reference list, and checking that figures are numbered and mentioned, are both old ideas
with several tools each** (below). What I could not find, as of October 2026, is a tool built for a **Persian `.docx` thesis** that does these together and understands Persian conventions:
chapter-based numbers such as `شکل ۲-۳` in three digit sets, `فصل دوم` chapter headings, Persian and Latin author-year entries in one list, Jalali years (`۱۳۹۸`) next to Gregorian ones,
`و همکاران` versus `et al.`. That is not a claim that no such tool exists anywhere (private tools, university scripts and Persian-language sites with no English description are invisible to my search);
if you know one, please open an issue and it will be linked here.

## Searches

GitHub repository search (API, total results; AND-of-terms and noisy):

| query | total |
|---|---|
| `docx citation checker bibliography` | 1 |
| `check citations against reference list docx` | 1 |
| `docx cross-reference checker figure table` | 0 |
| `unreferenced figures tables thesis checker` | 0 |
| `thesis docx linter python` | 1 |
| `persian thesis references checker` | 0 |
| `citation reference list mismatch checker word` | 0 |
| `docx dangling figure reference` | 0 |
| `farsi citation jalali year checker` | 0 |
| `پایان نامه منابع ارجاع بررسی` | 0 |
| `word thesis reference consistency author year` | 0 |
| `docx caption numbering checker` | 0 |
| `thesis reference checker Persian شکل جدول` | 0 |
| `checkcites` | 3 |
| `docx bibliography unused references` | 0 |

Also searched (2026-10-24): npm registry (`docx citation checker`, `thesis reference checker`, `docx cross reference`, `persian thesis`, `docx caption figure numbering`, `persian citation`, `jalali citation`:
only DOCX generators, `@citation-js/*`, Persian text and calendar libraries), PyPI index lookups for the names `arjaa`, `arjaa-cli` (free), and web searches
(`tool check figure table cross-references and citations vs reference list in Persian Farsi Word thesis docx 2026`, plus the Persian and English variants above).
I additionally searched GitHub for `Citation-Cross-Checker` by name after the web search surfaced it.

## Closest existing work

| project | what it is | difference |
|---|---|---|
| [okiratli/Citation-Cross-Checker](https://github.com/okiratli/Citation-Cross-Checker) | closest on the citation side: GUI and CLI, `.txt/.md/.docx/.pdf`, APA/Harvard/Chicago/MLA/IEEE/numeric, uncited references, year mismatches | **I ran it** (commit `00cda2d`) on arjaa's synthetic sample. It looks for a section called «References» unless you pass `--bib-section`; with `--bib-section "فهرست منابع"` it found the Latin citations and the unused entries, but took the second author («سارا») as the author of a Persian entry, did not report the Persian citation `(احمدی، ۱۴۰۱)` whose year differs from the entry, and has no figure/table checks, no chapter-based numbers, no Jalali/Gregorian rule. It does not claim Persian support. |
| [yorak/nyccc](https://github.com/yorak/nyccc) (2013) | name-year citation cross-checker for undefined/unused/mistyped citations | text input, English; no Word structure |
| [yemnick/academic-reference-checker](https://github.com/yemnick/academic-reference-checker), [zhongzhengshen/RefMatch-Skill](https://github.com/zhongzhengshen/RefMatch-Skill), [programmeratlarge/Citation_checker](https://github.com/programmeratlarge/Citation_checker) | agent skills and apps that compare in-text citations with the list in a `.docx` (RefMatch: APA-7, then web-searches missing sources; Citation_checker: looks references up online) | I read their READMEs, did not run them. English/APA oriented; RefMatch and Citation_checker use the web or an AI model, arjaa is offline and rule-based. None mention figures, tables, Persian or Jalali years. |
| [islandoftex/checkcites](https://github.com/islandoftex/checkcites) | Lua script for LaTeX: undefined/unused references in `.aux`/`.bib` | LaTeX only; if you write in XePersian/ParsiThesis, BibTeX already tells you this |
| [popfbi-bot/thesis-lint](https://github.com/popfbi-bot/thesis-lint) | Chinese thesis format check: fonts, margins, heading levels, references | formatting rules for Chinese theses, not cross-reference integrity; no Persian |
| CheckMyManuscript, RightMyWork, TypesetOS, hedwigai (web services) | upload-based checkers: figure and table numbering, unreferenced floats, citations vs list | online upload (a thesis is not something every student wants to upload), English-oriented, closed. I did not test them; claims are from their landing pages. |
| Word itself: Insert → Cross-reference, Table of Figures, Update Field (F9); Zotero, EndNote, Mendeley | keep numbers and bibliography in step *if* they were used from the start | no check on a finished file whose numbers were typed or pasted; reference managers fail silently on hand-typed citations. arjaa checks the file as it is, and tells you how many mentions are real cross-reference fields. |

## Verdict

Distinct combination: **offline, rule-based, Persian-aware integrity check of a `.docx` thesis: float numbering and mentions *and* citations against the reference list**, with Persian
digits, Jalali/Gregorian years, chapter-based numbers and `و همکاران`. Each half has an English-language counterpart; I did not find the Persian-aware combination. I did not run most of the
tools above; descriptions come from their own pages, and the one I ran (Citation-Cross-Checker) is an English-first tool that never claimed to support Persian, so its misses are not a criticism of it.
