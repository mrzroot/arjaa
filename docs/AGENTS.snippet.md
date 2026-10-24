<!-- Paste into AGENTS.md, CLAUDE.md, .cursorrules or your agent's rules file. Requires `pipx install git+https://github.com/mrzroot/arjaa`. -->

## Persian (Farsi) theses: figure numbers, mentions and citations

When asked to finish, proofread or "clean up" a Persian `.docx` thesis, check its cross-references before and after editing; a deleted figure or a pasted paragraph usually leaves a dangling mention
(«در شکل ۲-۳» with no figure 2-3) or a citation that is not in the reference list:

```sh
arjaa thesis.docx --map                # findings + every caption (where mentioned) + every reference entry (how often cited)
arjaa thesis.docx --json               # machine-readable
arjaa thesis.docx --strict             # exit 1 on warnings too
```

- Report the findings with their paragraph numbers; do not renumber captions or edit citations yourself. A caption made with Word's Insert → Caption carries a `SEQ` field: Word regenerates it (Ctrl+A, F9), so retyping its result does not stick.
- A finding is a heuristic, not a verdict: `(Johnson, 2017)` may be a source the author deliberately left out. Ask before deleting.
- Persian digits, Arabic-Indic digits and Latin digits are the same number to arjaa; do not "normalise" them just to silence a finding.
- It is not an official university validator, does not read footnotes, text boxes or Zotero/EndNote fields, and runs offline.
