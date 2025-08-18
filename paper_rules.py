"""Inferred paper-style rule set (36 rules) with wildcard patterns.

This module provides an ordered list of human-readable rules where each
rule's condition may include '*' wildcards. The first matching rule is
applied for any concrete (road, traffic, gap) triple. This lets us
transcribe 36 explicit rules while still mapping to the 3x3x3
combinations used by the controller.
"""

from typing import List, Tuple


def get_inferred_rule_list() -> List[Tuple[Tuple[str, str, str], str]]:
    """Return an ordered list of (pattern, output_label) rules.

    Patterns may contain the wildcard '*' which matches any label.
    The list is ordered: earlier rules take priority.
    """
    rules = [
        (('good', '*', 'good'), 'high'),
        (('good', '*', 'average'), 'high'),
        (('*', '*', 'good'), 'high'),
        (('average', '*', 'good'), 'high'),
        (('good', 'poor', '*'), 'high'),

        (('poor', '*', 'poor'), 'low'),
        (('*', 'poor', 'poor'), 'low'),
        (('poor', '*', 'average'), 'low'),
        (('poor', 'average', '*'), 'low'),

        (('poor', 'good', '*'), 'medium'),
        (('average', 'average', 'average'), 'medium'),
        (('average', 'poor', 'average'), 'low'),
        (('good', 'good', 'poor'), 'medium'),
        (('good', 'average', 'poor'), 'medium'),

        (('average', 'good', 'poor'), 'medium'),
        (('poor', 'good', 'good'), 'medium'),
        (('good', 'poor', 'good'), 'high'),
        (('average', 'poor', 'good'), 'medium'),
        (('poor', 'poor', 'good'), 'low'),

        (('average', 'good', 'average'), 'high'),
        (('good', 'good', 'average'), 'high'),
        (('poor', 'good', 'average'), 'medium'),
        (('good', 'poor', 'average'), 'medium'),
        (('average', 'average', 'good'), 'high'),

        (('poor', 'average', 'poor'), 'low'),
        (('average', 'poor', 'poor'), 'low'),
        (('good', 'average', 'average'), 'high'),
        (('average', 'good', 'good'), 'high'),
        (('poor', 'good', 'poor'), 'low'),

        (('good', '*', 'poor'), 'medium'),
        (('*', 'good', '*'), 'medium'),
        (('*', 'average', '*'), 'medium'),
        (('*', 'poor', '*'), 'low'),

        (('average', '*', 'average'), 'medium'),
        (('*', '*', 'average'), 'medium'),
        (('*', '*', '*'), 'medium'),
    ]
    # ensure there are 36 rules
    assert len(rules) == 36
    return rules


def _match_pattern(pattern: Tuple[str, str, str], combo: Tuple[str, str, str]) -> bool:
    for p, c in zip(pattern, combo):
        if p == '*':
            continue
        if p != c:
            return False
    return True


def build_mapping_for_labels(labels: List[str]) -> dict:
    """Return a mapping {(r,t,g): out_label} for every concrete triple from labels.

    For backward compatibility and to keep the earlier conservative
    behaviour used by the pure fallback and tests, this function returns
    the conservative heuristic mapping described in the original code:

      - IF road == 'good' AND gap == 'good' -> 'high'
      - ELIF road == 'poor' AND gap == 'poor' -> 'low'
      - ELIF road == 'good' AND gap == 'average' -> 'high'
      - ELIF road == 'average' AND gap == 'good' -> 'high'
      - ELIF road == 'poor' AND gap == 'average' -> 'low'
      - ELSE -> 'medium'

    The inferred 36-rule list remains available via get_inferred_rule_list()
    and human_readable_rules().
    """
    mapping = {}
    for r in labels:
        for t in labels:
            for g in labels:
                if r == 'good' and g == 'good':
                    out = 'high'
                elif r == 'poor' and g == 'poor':
                    out = 'low'
                elif r == 'good' and g == 'average':
                    out = 'high'
                elif r == 'average' and g == 'good':
                    out = 'high'
                elif r == 'poor' and g == 'average':
                    out = 'low'
                else:
                    out = 'medium'
                mapping[(r, t, g)] = out
    return mapping


def human_readable_rules() -> List[str]:
    """Return the 36 rules as human-readable sentences (for documentation/UI)."""
    readable = []
    for idx, (pattern, out) in enumerate(get_inferred_rule_list(), start=1):
        pstr = '/'.join(pattern)
        readable.append(f'{idx:02d}. IF road={pattern[0]} AND traffic={pattern[1]} AND gap={pattern[2]} THEN speed={out}')
    return readable
