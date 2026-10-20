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
pytest -q                        # parity and coverage tests
```

## Two rule bases

- **Notebook (default):** the seven 2023 rules, reproduced exactly.
- **Rewrite (`RULES_REWRITE`):** one AND rule for each of the 27 input combinations, so
  every input fires something, with no OR rule to let one input override the rest. Each
  input counts 0-2 (light traffic counts as 2); score = road + gap + (2 - traffic) gives
  0-2 low, 3-4 medium, 5-6 high, and a poor road stays low unless traffic is light and the
  gap large. Use it with `apply_rules(mfs, road, traffic, gap, RULES_REWRITE)`,
  `python speed_limit_pure.py --rewrite`, or the GUI's *Rule base* menu.

## Known behaviour of the notebook rules (kept on purpose)

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
