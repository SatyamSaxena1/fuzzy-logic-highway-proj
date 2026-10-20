# Fuzzy Logic Highway Project

A fuzzy-logic speed-limit advisor from my MSc Fuzzy Logic coursework (Jul 2023).
Three inputs on a 0-10 scale (road conditions, traffic density, gap in traffic)
go through seven Mamdani rules to a recommended speed limit on 0-100.

**Try it in the browser:** https://blinkedit.me/fuzzy/

## Files

- `Fuzzy_logic_speed_limit_v2.ipynb` - the original notebook, built with `scikit-fuzzy`.
- `speed_limit_pure.py` - the same system in NumPy only (no scikit-fuzzy). Matches
  `skfuzzy.control` to floating-point precision, including defuzzification.
- `speed_limit_gui.py` - a Tkinter + matplotlib GUI on top of `speed_limit_pure.py`.
- `test_speed_limit_pure.py` - checks `speed_limit_pure.py` against reference outputs
  produced by scikit-fuzzy 0.5 running the notebook.
- `Fuzzy logic.docx` - the group report this work came from.

## Quick start

```powershell
pip install -r requirements.txt
python .\speed_limit_pure.py     # console version
python .\speed_limit_gui.py      # GUI
pytest -q                        # parity tests
```

## Known behaviour (kept on purpose, it matches the notebook)

- Rule 1 joins its conditions with OR, so dense traffic alone forces a low limit
  (perfect road, dense traffic and a big gap gives 16.7).
- Seven rules do not cover every combination. Some inputs fire no rule at all,
  for example road 10, traffic 0, gap 5. scikit-fuzzy raises `KeyError: 'speed_limit'`
  there; `speed_limit_pure.apply_rules` returns `None`.
- `automf(3)` names every input's terms poor / average / good by value, so for
  traffic density "good" means heavy traffic.

## Credits

The notebook uses [scikit-fuzzy](https://github.com/scikit-fuzzy/scikit-fuzzy)
(BSD 3-Clause, Copyright (c) 2012, the scikit-fuzzy team). The defuzzification in
`speed_limit_pure.py` reimplements scikit-fuzzy's method so results match. Earlier
commits of this repository included `fuzzy_logic.py`, a copy of scikit-fuzzy's fuzzy
set operations; it has been removed as unused.
