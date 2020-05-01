"""This module contains various operations on automata."""

import collections
from . import machines
from . import syntax

def determinize(m):
    """Determinizes a finite automaton."""
    if not m.is_finite():
        raise TypeError("machine must be a finite automaton")

    transitions = collections.defaultdict(lambda: collections.defaultdict(set))
    alphabet = set()
    for transition in m.get_transitions():
        [[lstate], read] = transition.lhs
        [[rstate]] = transition.rhs
        if len(read) > 1:
            raise NotSupportedException("multiple input symbols on transition not supported")
        if len(read) == 1:
            alphabet.add(read[0])
        transitions[lstate][tuple(read)].add(rstate)

    def eclosure(states):
        """Find epsilon-closure of set of states."""
        states = set(states)
        frontier = set(states)
        while len(frontier) > 0:
            lstate = frontier.pop()
            for rstate in transitions[lstate][()]:
                if rstate not in states:
                    states.add(rstate)
                    frontier.add(rstate)
        return states

    dm = machines.FiniteAutomaton()

    start_state = syntax.Set(eclosure([m.get_start_state()]))
    dm.set_start_state(start_state)

    frontier = {start_state}
    visited = set()
    while len(frontier) > 0:
        lstates = frontier.pop()
        if lstates in visited:
            continue
        visited.add(lstates)
        dtransitions = collections.defaultdict(set)
        for lstate in lstates:
            for read in alphabet:
                dtransitions[read] |= transitions[lstate][(read,)]
        for read in alphabet:
            rstates = syntax.Set(eclosure(dtransitions[read]))
            dm.add_transition([[lstates], read], [[rstates]])
            frontier.add(rstates)

    accept_states = set(m.get_accept_states())
    for states in visited:
        if len(states & accept_states) > 0:
            dm.add_accept_state(states)

    return dm

def equivalent(m1, m2):
    """Test whether two DFAs are equivalent, using the Hopcroft-Karp algorithm."""
    if not m1.is_finite() and m1.is_deterministic():
        raise TypeError("machine must be a deterministic finite automaton")
    if not m2.is_finite() and m2.is_deterministic():
        raise TypeError("machine must be a deterministic finite automaton")

    # Index transitions. We use tuples (1,q) and (2,q) to rename apart state sets
    alphabet = set()
    d = {}
    for t in m1.get_transitions():
        [[q], a] = t.lhs
        [[r]] = t.rhs
        alphabet.add(a)
        d[(1,q),a] = (1,r)
    for t in m2.get_transitions():
        [[q], a] = t.lhs
        [[r]] = t.rhs
        alphabet.add(a)
        d[(2,q),a] = (2,r)

    # Naive union find data structure
    u = {}
    def union(x, y):
        for z in u:
            if u[z] == x:
                u[z] = y

    for q in m1.states:
        u[1,q] = (1,q)
    for q in m2.states:
        u[2,q] = (2,q)

    s = []

    s1 = (1,m1.get_start_state())
    s2 = (2,m2.get_start_state())
    union(s1, s2)
    s.append((s1, s2))

    while len(s) > 0:
        q1, q2 = s.pop()
        for a in alphabet:
            r1 = u[d[q1,a]]
            r2 = u[d[q2,a]]
            if r1 != r2:
                union(r1, r2)
                s.append((r1, r2))

    cls = {}
    f = ( {(1, q) for q in m1.get_accept_states()} | 
          {(2, q) for q in m2.get_accept_states()} )

    for q in u:
        if u[q] not in cls:
            cls[u[q]] = q in f
        elif (q in f) != cls[u[q]]:
            return False
    return True

def intersect(m1, m2):
    """Intersect two Machines.

    Both machines should have a state as store 0 and input STREAM as
    store 1. For example, 

    - Both can be finite automata, in which case this is the standard
      product construction.

    - One can be an NFA and the other a PDA, in which case the result
      is a PDA.

    - The intersection of two PDAs would be a two-stack PDA.
    """

    def make_tuple(*xs):
        return syntax.Tuple(xs)

    def is_finite_plus(m):
        return (m.store_types[:2] == (machines.BASE, machines.STREAM) and
                m.state == 0 and m.has_cell(0) and
                m.input == 1 and m.has_input_stream(1))

    if not is_finite_plus(m1):
        raise ValueError("m1 must have a state and input stream")
    if not is_finite_plus(m2):
        raise ValueError("m2 must have a state and input stream")
    for t1 in m1.transitions:
        if len(t1.lhs[1]) > 1:
            raise ValueError('m1 cannot have multiple input symbols on a transition')
    for t2 in m2.transitions:
        if len(t2.lhs[1]) > 1:
            raise ValueError('m2 cannot have multiple input symbols on a transition')

    store_types = ((machines.BASE, machines.STREAM) +
                   m1.store_types[2:] + m2.store_types[2:])

    m = machines.Machine(store_types, state=0, input=1)

    m.start_config = machines.Configuration(
        ([make_tuple(m1.start_config[0][0], m2.start_config[0][0])], []) +
        m1.start_config[2:] + m2.start_config[2:]
    )


    for c1 in m1.accept_configs:
        for c2 in m2.accept_configs:
            m.accept_configs.add(machines.Configuration(
                ([make_tuple(c1[0][0], c2[0][0])], [syntax.BLANK]) + c1[2:] + c2[2:]
            ))
            
    for t1 in m1.transitions:
        for t2 in m2.transitions:
            if t1.lhs[1] == t2.lhs[1] and len(t1.lhs[1]) > 0:
                m.transitions.append(machines.Transition(
                    ([make_tuple(t1.lhs[0][0], t2.lhs[0][0])], t1.lhs[1]) + t1.lhs[2:] + t2.lhs[2:],
                    ([make_tuple(t1.rhs[0][0], t2.rhs[0][0])], []) + t1.lhs[2:] + t2.lhs[2:],
                ))

    # Handle epsilon transitions. For stores 2 and beyond, we just use
    # a lhs and rhs of &, whether or not this makes sense for the type
    # of automaton that m1 and m2 are.
    for t1 in m1.transitions:
        if len(t1.lhs[1]) == 0:
            for q2 in m2.states:
                m.transitions.append(machines.Transition(
                    ([make_tuple(t1.lhs[0][0], q2)], []) + ([],)*(m.num_stores-2),
                    ([make_tuple(t1.rhs[0][0], q2)], []) + ([],)*(m.num_stores-2)
                ))

    for t2 in m2.transitions:
        if len(t2.lhs[1]) == 0:
            for q1 in m1.states:
                m.transitions.append(machines.Transition(
                    ([make_tuple(q1, t2.lhs[0][0])], []) + ([],)*(m.num_stores-2),
                    ([make_tuple(q1, t2.rhs[0][0])], []) + ([],)*(m.num_stores-2)
                ))

    return m

def prefix(m):
    """Given a NFA `m`, construct a new NFA that accepts all prefixes of
    strings accepted by `m`.
    """
    if not m.is_finite():
        raise ValueError('m must be a finite automaton')
    f = set(m.get_accept_states())
    size = None
    while len(f) != size:
        size = len(f)
        for t in m.get_transitions():
            [[q], [a]], [[r]] = t.lhs, t.rhs
            if r in f:
                f.add(q)
    mp = machines.FiniteAutomaton()
    mp.set_start_state(m.get_start_state())
    for t in m.get_transitions():
        mp.add_transition(t)
    mp.add_accept_states(f)
    return mp

