"""A pure-Python (NumPy only) version of the speed-limit system in
`Fuzzy_logic_speed_limit_v2.ipynb`, with no scikit-fuzzy dependency.

It uses the notebook's own design: three inputs on 0-10 with automf(3)
triangles (poor / average / good), an output on 0-100 with three triangles,
the notebook's seven rules, Mamdani min/max inference and centroid
defuzzification. The defuzzification follows scikit-fuzzy 0.5 step for step
(cut-level crossing points are added to the universe, then a piecewise-linear
centroid), so results match `skfuzzy.control` to floating-point precision.
See test_speed_limit_pure.py.

Like the notebook, some inputs fire no rule at all (for example road 10,
traffic 0, gap 5). scikit-fuzzy raises KeyError('speed_limit') there;
this module returns None instead.
"""

import numpy as np

UNI_IN = np.arange(0, 11, 1)
UNI_OUT = np.arange(0, 101, 1)
LABELS = ('poor', 'average', 'good')

# (operator, (road, traffic, gap), output), exactly as in the notebook
RULES = [
    ('or', ('poor', 'good', 'poor'), 'low'),
    ('and', ('poor', 'average', 'average'), 'low'),
    ('and', ('average', 'good', 'poor'), 'low'),
    ('and', ('average', 'average', 'average'), 'medium'),
    ('and', ('good', 'good', 'poor'), 'medium'),
    ('and', ('good', 'average', 'average'), 'high'),
    ('and', ('good', 'poor', 'good'), 'high'),
]


def _rewrite_rules():
    """A 2026 rewrite: one AND rule for each of the 27 combinations, so every input fires.

    Each input counts 0/1/2 (traffic counts in reverse, since light traffic helps).
    Score = road + gap + (2 - traffic): 0-2 low, 3-4 medium, 5-6 high. A poor road
    stays low unless traffic is light and the gap is large (then medium).
    """
    rules = []
    for ri, r in enumerate(LABELS):
        for ti, t in enumerate(LABELS):
            for gi, g in enumerate(LABELS):
                s = ri + gi + (2 - ti)
                out = 'low' if s <= 2 else 'medium' if s <= 4 else 'high'
                if ri == 0:
                    out = 'medium' if (ti == 0 and gi == 2) else 'low'
                rules.append(('and', (r, t, g), out))
    return rules


RULES_REWRITE = _rewrite_rules()

# the rewrite reads the same terms with names that match their meaning
REWRITE_NAMES = ({}, {'poor': 'light', 'average': 'moderate', 'good': 'heavy'},
                 {'poor': 'small', 'average': 'medium', 'good': 'large'})


def trimf(x, abc):
    """Triangular membership function, same as skfuzzy.trimf."""
    a, b, c = abc
    y = np.zeros(len(x))
    if a != b:
        idx = (a < x) & (x < b)
        y[idx] = (x[idx] - a) / (b - a)
    if b != c:
        idx = (b < x) & (x < c)
        y[idx] = (c - x[idx]) / (c - b)
    y[x == b] = 1.0
    return y


def build_speed_mfs():
    """Membership functions keyed by term name, plus the two universes."""
    lo, hi = UNI_IN[0], UNI_IN[-1]
    mid = (lo + hi) / 2
    return {
        'uni_in': UNI_IN,
        'uni_out': UNI_OUT,
        # automf(3)
        'poor': trimf(UNI_IN, [lo, lo, mid]),
        'average': trimf(UNI_IN, [lo, mid, hi]),
        'good': trimf(UNI_IN, [mid, hi, hi]),
        # notebook output terms
        'low': trimf(UNI_OUT, [0, 0, 50]),
        'medium': trimf(UNI_OUT, [0, 50, 100]),
        'high': trimf(UNI_OUT, [50, 100, 100]),
    }


def _centroid(x, mfx):
    """Piecewise-linear centroid, same as skfuzzy.defuzzify.centroid."""
    sum_moment_area = sum_area = 0.0
    for i in range(1, len(x)):
        x1, x2, y1, y2 = x[i - 1], x[i], mfx[i - 1], mfx[i]
        if (y1 == 0 and y2 == 0) or x1 == x2:
            continue
        if y1 == y2:
            moment, area = 0.5 * (x1 + x2), (x2 - x1) * y1
        elif y1 == 0:
            moment, area = 2 / 3 * (x2 - x1) + x1, 0.5 * (x2 - x1) * y2
        elif y2 == 0:
            moment, area = 1 / 3 * (x2 - x1) + x1, 0.5 * (x2 - x1) * y1
        else:
            moment = (2 / 3 * (x2 - x1) * (y2 + 0.5 * y1)) / (y1 + y2) + x1
            area = 0.5 * (x2 - x1) * (y1 + y2)
        sum_moment_area += moment * area
        sum_area += area
    return sum_moment_area / sum_area


def _crossings(x, mf, cut):
    """x positions where a term's membership crosses its cut level."""
    d = mf - cut
    i = np.nonzero(d[:-1] * d[1:] < 0)[0]
    return x[i] + (x[i + 1] - x[i]) * d[i] / (d[i] - d[i + 1])


def compute(mfs, rc_val, td_val, gap_val, rules_set=RULES):
    """Run a rule base (the notebook's RULES by default, or RULES_REWRITE).

    Returns (speed or None, x, aggregated_mf, rules), where rules is a list of
    (description, activation, clipped_mf_on_x) sorted by activation.
    """
    ui = mfs['uni_in']
    fuzz = [{t: float(np.interp(v, ui, mfs[t])) for t in LABELS} for v in (rc_val, td_val, gap_val)]

    cut = {'low': 0.0, 'medium': 0.0, 'high': 0.0}
    activations = []
    for op, terms, out in rules_set:
        vals = [fuzz[i][t] for i, t in enumerate(terms)]
        act = max(vals) if op == 'or' else min(vals)
        activations.append(act)
        cut[out] = max(cut[out], act)

    # scikit-fuzzy evaluates the output on the universe plus each cut crossing
    uo = mfs['uni_out']
    x = np.unique(np.concatenate([uo] + [_crossings(uo, mfs[k], c) for k, c in cut.items() if 0 < c < 1]))

    rules, agg = [], np.zeros(len(x))
    for (op, terms, out), act in zip(rules_set, activations):
        clipped = np.fmin(act, np.interp(x, uo, mfs[out]))
        agg = np.fmax(agg, clipped)
        desc = _describe(op, terms, out, rules_set)
        rules.append((desc, act, clipped))
    rules.sort(key=lambda r: r[1], reverse=True)

    speed = _centroid(x, agg) if agg.any() else None
    return speed, x, agg, rules


def _describe(op, terms, out, rules_set):
    names = REWRITE_NAMES if rules_set is RULES_REWRITE else ({}, {}, {})
    t = [names[i].get(term, term) for i, term in enumerate(terms)]
    j = ' OR ' if op == 'or' else ' AND '
    return f'road {t[0]}{j}traffic {t[1]}{j}gap {t[2]} -> {out}'


def apply_rules(mfs, rc_val, td_val, gap_val, rules_set=RULES):
    """Recommended speed limit, or None when no rule fires."""
    return compute(mfs, rc_val, td_val, gap_val, rules_set)[0]


def human_readable_rules(rules_set=RULES):
    """A rule base as numbered sentences (for documentation/UI)."""
    return [f'{i}. IF ' + _describe(op, terms, out, rules_set).replace(' -> ', ' THEN speed is ')
            for i, (op, terms, out) in enumerate(rules_set, start=1)]


def main():
    import sys
    mfs = build_speed_mfs()
    rules_set = RULES_REWRITE if '--rewrite' in sys.argv else RULES
    print('Fuzzy speed limit (' + ('27-rule rewrite' if rules_set is RULES_REWRITE else 'notebook rules') + ', no scikit-fuzzy). Ctrl+C to quit.')
    while True:
        try:
            rc = float(input('Enter road conditions (0-10): '))
            td = float(input('Enter traffic density (0-10): '))
            gap = float(input('Enter gap in traffic (0-10): '))
            if not (0 <= rc <= 10 and 0 <= td <= 10 and 0 <= gap <= 10):
                print('Inputs must be between 0 and 10')
                continue
            out = apply_rules(mfs, rc, td, gap, rules_set)
            print('No rule fires for these inputs.' if out is None else f'Recommended speed limit: {out:.2f}')
        except ValueError:
            print('Please enter a number.')
        except (KeyboardInterrupt, EOFError):
            print()
            break


if __name__ == '__main__':
    main()
