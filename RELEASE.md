Release guidance

Ship a lightweight release by attaching these files to the GitHub Release:

- `speed_limit_gui.py`  (GUI)
- `speed_limit_pure.py` (the engine the GUI imports)
- `README.md`           (usage and quick start)
- `requirements.txt`    (runtime deps)

If you need a Windows executable, build it outside of the repo (CI job) and attach the artifact to the release rather than committing `dist/` or `build/` folders into source control.
