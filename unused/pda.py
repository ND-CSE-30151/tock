# Based on: Bernard Lang, "Deterministic techniques for efficient
# non-deterministic parsers." doi:10.1007/3-540-06841-4_65

import collections

"""
Cubic-time recognizer for nondeterministic PDAs.
This could be made more general: Allow a "tail_sharing=2" option, which means that item stores store 2 only up to head, plus a back-pointer
- item equivalency is 1-deep
- inference rules should not look inside back-pointer
"""

"""Transitions are of the form
   (q, pop, a, r, push), where 
   - q and r are states
   - a is an input symbol (or None = epsilon)
   - pop and push are stack symbols (or None = epsilon)

   This example recognizes all strings that are *not* of the form ww.
"""

initial_state = "q0"
final_states = ["qf"]
transitions = [
    ("q0", None, None, "q1", "$"),
    ("q1", None, "a", "q1", "*"),
    ("q1", None, "b", "q1", "*"),
    ("q1", None, "a", "q2a", None),
    ("q1", None, "b", "q2b", None),
    ("q2a", "*", "a", "q2a", None),
    ("q2a", "*", "b", "q2a", None),
    ("q2b", "*", "a", "q2b", None),
    ("q2b", "*", "b", "q2b", None),
    ("q2a", "$", None, "q3a", "$"),
    ("q2b", "$", None, "q3b", "$"),
    ("q3a", None, "a", "q3a", "*"),
    ("q3a", None, "b", "q3a", "*"),
    ("q3b", None, "a", "q3b", "*"),
    ("q3b", None, "b", "q3b", "*"),
    ("q3a", None, "b", "q4", None),
    ("q3b", None, "a", "q4", None),
    ("q4", "*", "a", "q4", None),
    ("q4", "*", "b", "q4", None),
    ("q4", "$", None, "qf", None),
]

# Index the transitions
transitions_index = collections.defaultdict(list)
for (q, x, a, r, y) in transitions:
    transitions_index[q, x, a].append((r, y))

w = "a a a b a a a a a a".split()

"""Items are of the form (q, x, i -> r, y, j), where
   - q and r are states
   - x and y are stack symbols (or $)

   The meaning of this item is that on reading input w[i:j], the
   machine can go from configuration (q, Sx) to configuration (r, Sxy)."""

BOT1 = -1
BOT2 = -2

agenda = collections.defaultdict(list)
chart_left = collections.defaultdict(set)
chart_right = collections.defaultdict(set)

def add(item):
    q, x, i, r, y, j = item
    if item in chart_left[q, x, i]: return
    agenda[j].append(item)
    chart_left[q, x, i].add(item)
    chart_right[r, y, j].add(item)
    print "[%d] Add: %s" % (sum(len(c) for c in chart_left.values()), item)

# Axiom
add((initial_state, BOT2, 0, initial_state, BOT1, 0))

for j in xrange(len(w)+1):
    while len(agenda[j]) > 0:
        trigger = agenda[j].pop(0)
        tq, tx, ti, tr, ty, tj = trigger
        print "Trigger:", trigger

        # Goal
        if (tq == initial_state and tx == BOT2 and ti == 0 and 
            tr in final_states and ty == BOT1 and tj == len(w)):
            print "Goal!"
            break

        transitions = [(r, y, tj) for (r, y) in transitions_index[tr, None, None]]
        if tj < len(w):
            transitions.extend([(r, y, tj+1) for (r, y) in transitions_index[tr, None, w[tj]]])

        for (r, y, nj) in transitions:
            # No-op
            if y is None:
                add((tq, tx, ti, r, ty, nj))

            # Push (like Earley predict)
            else:
                add((tr, ty, tj, r, y, nj))

        transitions = [(r, y, tj) for (r, y) in transitions_index[tr, ty, None]]
        if tj < len(w):
            transitions.extend([(r, y, tj+1) for (r, y) in transitions_index[tr, ty, w[tj]]])

        for (r, y, nj) in transitions:
            # Pop (like Earley complete)
            if y is None:
                for pitem in chart_right[tq, tx, ti]:
                    pq, px, pi, _, _, _ = pitem
                    add((pq, px, pi, r, tx, nj))

            # Pop-push
            else:
                add((tq, tx, ti, r, y, nj))

        # Pop. This case is only needed when the child item and transition both don't scan, because the agenda is ordered by j
        for citem in chart_left[tr, ty, tj]:
            _, _, _, cr, cy, cj = citem
            if tj == cj: # non-scanning
                for (r, y) in transitions_index[cr, cy, None]:
                    if y is None: # pop
                        add((tq, tx, ti, r, ty, tj))
