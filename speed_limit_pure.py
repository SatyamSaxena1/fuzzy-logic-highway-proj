"""A pure-Python fuzzy speed limit tester that doesn't require scikit-fuzzy.

Uses simple triangular membership functions and the `fuzzy_logic` helpers
already present in the repo for basic set operations.
"""

import sys
import numpy as np
from fuzzy_logic import fuzzy_and, fuzzy_or, fuzzy_not
from paper_rules import build_mapping_for_labels


def trimf(x, abc):
    a, b, c = abc
    y = np.zeros_like(x, dtype=float)
    # rising edge
    idx = (x >= a) & (x <= b)
    if b != a:
        y[idx] = (x[idx] - a) / (b - a)
    # falling edge
    idx = (x >= b) & (x <= c)
    if c != b:
        y[idx] = (c - x[idx]) / (c - b)
    return y


def interp_membership(x, mf, value):
    return np.interp(value, x, mf)


def build_speed_mfs():
    # universes
    uni_in = np.arange(0, 11, 1)
    uni_out = np.arange(0, 121, 1)

    # helper: trapezoidal MF like skfuzzy.trapmf
    def trapmf(x, abcd):
        a, b, c, d = abcd
        y = np.zeros_like(x, dtype=float)
        # rising edge
        idx = (x >= a) & (x <= b)
        if b != a:
            y[idx] = (x[idx] - a) / (b - a)
        # top
        idx = (x >= b) & (x <= c)
        y[idx] = 1.0
        # falling edge
        idx = (x >= c) & (x <= d)
        if d != c:
            y[idx] = (d - x[idx]) / (d - c)
        return y

    def gauss(x, mu, sigma):
        return np.exp(-0.5 * ((x - mu) / sigma) ** 2)

    # Input membership functions (poor, average, good) use trapezoids per report
    poor = trapmf(uni_in, [0, 0, 2, 3])
    average = trapmf(uni_in, [2, 4, 6, 8])
    good = trapmf(uni_in, [5, 8, 10, 10])

    # Gaussian outputs (centers 15,45,90; tuned sigma)
    low = gauss(uni_out, 15, 10)
    medium = gauss(uni_out, 45, 12)
    high = gauss(uni_out, 90, 15)

    mfs = {
        'uni_in': uni_in,
        'uni_out': uni_out,
        'poor': poor,
        'average': average,
        'good': good,
        'low': low,
        'medium': medium,
        'high': high,
    }
    return mfs


def apply_rules(mfs, rc_val, td_val, gap_val):
    ui = mfs['uni_in']
    uo = mfs['uni_out']

    # fuzzify inputs
    rc = np.array([interp_membership(ui, mfs['poor'], rc_val), interp_membership(ui, mfs['average'], rc_val), interp_membership(ui, mfs['good'], rc_val)])
    td = np.array([interp_membership(ui, mfs['poor'], td_val), interp_membership(ui, mfs['average'], td_val), interp_membership(ui, mfs['good'], td_val)])
    gap = np.array([interp_membership(ui, mfs['poor'], gap_val), interp_membership(ui, mfs['average'], gap_val), interp_membership(ui, mfs['good'], gap_val)])

    # Programmatic rule aggregation mirroring CLI heuristic
    # provide an explicit rule table (exhaustive 3x3x3 = 27 combinations)
    # Keys: (road, traffic, gap) values are one of 'low','medium','high'
    # This explicit mapping is easier to review and mirrors the heuristic used before.
    # use the inferred 36-rule mapping module to build an explicit mapping
    labels = ['poor', 'average', 'good']
    mapping = build_mapping_for_labels(labels)

    low_act = 0.0
    medium_act = 0.0
    high_act = 0.0
    labels = ['poor', 'average', 'good']
    for i, rlab in enumerate(labels):
        for j, tlab in enumerate(labels):
            for k, glab in enumerate(labels):
                r_val = rc[i]
                t_val = td[j]
                g_val = gap[k]
                activation = min(r_val, t_val, g_val)
                out_label = mapping[(rlab, tlab, glab)]
                if out_label == 'low':
                    low_act = max(low_act, activation)
                elif out_label == 'medium':
                    medium_act = max(medium_act, activation)
                else:
                    high_act = max(high_act, activation)

    # apply clipping to output MFs
    low_clip = np.fmin(low_act, mfs['low'])
    medium_clip = np.fmin(medium_act, mfs['medium'])
    high_clip = np.fmin(high_act, mfs['high'])

    # aggregate final mf
    agg = np.fmax(low_clip, np.fmax(medium_clip, high_clip))

    # defuzzify using centroid
    if agg.sum() == 0:
        centroid = 0.0
    else:
        centroid = (agg * mfs['uni_out']).sum() / agg.sum()

    return centroid


def main():
    mfs = build_speed_mfs()
    print('Pure-Python fuzzy speed limit tester (no scikit-fuzzy).')
    try:
        rc = float(input('Enter road conditions (0-10): '))
        td = float(input('Enter traffic density (0-10): '))
        gap = float(input('Enter gap in traffic (0-10): '))
        if not (0 <= rc <= 10 and 0 <= td <= 10 and 0 <= gap <= 10):
            print('Inputs must be between 0 and 10')
            return
        out = apply_rules(mfs, rc, td, gap)
        print(f'Recommended speed limit: {out:.2f}')
    except Exception as e:
        print('Error:', e)


if __name__ == '__main__':
    main()
