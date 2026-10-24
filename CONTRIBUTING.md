# Contributing

Thanks for helping! arjaa is small on purpose: standard library only, no telemetry, no network.

```sh
git clone https://github.com/mrzroot/arjaa && cd arjaa
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest
python -m arjaa --demo
```

Ground rules

- **No new runtime dependencies**, and Python 3.9 must keep working.
- Tests use synthetic, generated `.docx` fixtures only. Never commit a real thesis or any real person's document.
- A rule must prefer silence to a wrong accusation: if a mention or a citation cannot be recognised with confidence, it is not reported. Add a test with a case that must **not** fire next to the one that must.
- Add your change to `CHANGELOG.md`.
- Found a tool that already does this? Open an issue; it will be linked in the README and NOVELTY.md.
