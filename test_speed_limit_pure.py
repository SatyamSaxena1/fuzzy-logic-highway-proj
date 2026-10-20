"""speed_limit_pure must reproduce the notebook as run by scikit-fuzzy 0.5.

Reference values were produced by running the notebook's exact Antecedent,
Consequent and Rule definitions through skfuzzy.control. Run: pytest -q
"""

import pytest

from speed_limit_pure import RULES_REWRITE, apply_rules, build_speed_mfs

# (road, traffic, gap, skfuzzy output); None means skfuzzy raises KeyError('speed_limit')
REFERENCE = [
    (5, 5, 5, 50.0),
    (10, 0, 10, 83.3333),
    (10, 5, 5, 83.3333),
    (0, 10, 0, 16.6667),
    (7.5, 2.5, 9, 62.971),
    (10, 10, 10, 16.6667),
    (8, 3, 6, 58.7805),
    (2, 4, 5, 41.2195),
    (10, 0, 5, None),
    (6, 4, 6, 50.9524),
]


@pytest.mark.parametrize('road, traffic, gap, expected', REFERENCE)
def test_matches_scikit_fuzzy(road, traffic, gap, expected):
    got = apply_rules(build_speed_mfs(), road, traffic, gap)
    if expected is None:
        assert got is None
    else:
        assert got == pytest.approx(expected, abs=1e-3)


def test_rewrite_covers_every_input():
    mfs = build_speed_mfs()
    assert len(RULES_REWRITE) == 27
    steps = [i / 2 for i in range(21)]
    for r in steps:
        for t in steps:
            for g in steps:
                assert apply_rules(mfs, r, t, g, RULES_REWRITE) is not None, (r, t, g)


def test_rewrite_fixes_the_notebook_failures():
    mfs = build_speed_mfs()
    # same values as the browser engine (assets/js/fuzzy-engine.js on blinkedit.me/fuzzy)
    assert apply_rules(mfs, 10, 0, 5, RULES_REWRITE) == pytest.approx(83.3333, abs=1e-3)   # notebook: no rule fires
    assert apply_rules(mfs, 10, 10, 10, RULES_REWRITE) == pytest.approx(50.0, abs=1e-3)    # notebook: 16.7
    assert apply_rules(mfs, 0, 10, 0, RULES_REWRITE) < 20 < 80 < apply_rules(mfs, 10, 0, 10, RULES_REWRITE)


def test_traffic_density_matters():
    # the previous mapping ignored traffic entirely; dense traffic must now lower the limit
    mfs = build_speed_mfs()
    assert apply_rules(mfs, 10, 10, 10) < apply_rules(mfs, 10, 0, 10)
