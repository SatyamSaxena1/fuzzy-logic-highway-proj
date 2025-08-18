# Fuzzy Logic Highway Project

This repository contains a simple fuzzy-logic speed-limit demonstrator.

Files of interest
- `fuzzy_logic.py` - utility functions for fuzzy set operations.
- `Fuzzy_logic_speed_limit_v2.ipynb` - original notebook using `scikit-fuzzy`.
- `speed_limit_cli.py` - CLI using `scikit-fuzzy` control module (needs scikit-fuzzy).
- `speed_limit_pure.py` - pure-Python fallback implementation (no external fuzzy lib required).
- `speed_limit_gui.py` - lightweight Tkinter GUI that embeds matplotlib and uses the pure-Python controller.

Quick start

1) Run the pure-Python demo (no extra installs):

```powershell
python .\speed_limit_pure.py
```

2) To run the GUI (recommended lightweight release artifact):

The Tkinter GUI is a single Python script (`speed_limit_gui.py`) that uses the pure-Python controller and matplotlib to plot MFs and results.

Install the runtime dependencies and run:

```powershell
pip install numpy matplotlib
python .\speed_limit_gui.py
```

Optional: install `scikit-fuzzy` only if you want to run the richer CLI (`speed_limit_cli.py`) or reproduce the original notebook.

Note: the project uses an output speed range of 0-120 km/h to match the project report.

Tests

A small unit test is included to exercise the pure-Python runner. Run with:

```powershell
pip install pytest
pytest -q
```

Releases / distribution

For releases we recommend attaching the single script `speed_limit_gui.py` and the `README.md`. This keeps the release lightweight and avoids bundling large native dependencies. If you need a bundled executable, keep the old `build/` and `dist/` artifacts out of source control and generate them in CI or locally using a build script outside the repo.

Maintaining GitHub docs

- Edit this `README.md` for repository-level docs.
- Add more `.md` files under a `docs/` folder for longer documentation.
- Keep the notebook in the repo for interactive exploration; convert it to a script for CI-friendly runs.

Contact

Open an issue or push a PR to iterate on features.
