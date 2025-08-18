Release guidance

Ship a lightweight release by attaching these files to the GitHub Release:

- `speed_limit_gui.py`  (single-file GUI to attach)
- `README.md`           (usage and quick start)
- `requirements.txt`    (runtime deps)

Optional: include `speed_limit_pure.py` and `paper_rules.py` if you want users to inspect or run the pure fallback directly.

If you need a Windows executable, build it outside of the repo (CI job) and attach the artifact to the release rather than committing `dist/` or `build/` folders into source control.
