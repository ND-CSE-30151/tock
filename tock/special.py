from . import machines
from .syntax import START, ACCEPT, REJECT, BLANK

"""These convenience functions get/set the fake transition from START
to an initial state."""

def set_initial_state(m, q, n=None):
    # to do: eliminate n argument
    if get_initial_state(m):
        raise ValueError("machine can only have one start state")
    if n is None:
        n = m.num_stores
    lhs = [machines.Store([START])] + [machines.Store()]*(n-1)
    rhs = [machines.Store([q])] + [machines.Store()]*(n-1)
    m.add_transition(machines.Transition(lhs, rhs))

def get_initial_state(m):
    """Returns the initial state of m, or None if there is none."""
    initial_states = set()
    for t in m.transitions:
        if list(t.lhs[0]) == [START]:
            if (sum(len(store) for store in t.lhs) +
                sum(len(store) for store in t.rhs)) == 2:
                initial_states.add(t.rhs[0][0])
            else:
                # machine has an explicit transition from START
                return None
    if len(initial_states) == 1:
        return initial_states.pop()
    else:
        return None

"""These convenience functions apply only to Machines m such that
m.has_input(1) is true."""

def add_transition(m, l, r):
    # If necessary, supply implicit rhs for input,
    # which is always the *second* store
    if len(r) == len(l)-1:
        r = list(r)
        r[1:1] = [machines.Store()]
    m.add_transition(machines.Transition(l, r))

def get_transitions(m):
    one_way_input = m.has_input(1)
    for t in m.transitions:
        lhs, rhs = t.lhs, t.rhs
        if one_way_input:
            rhs = rhs[0:1] + rhs[2:]
        yield lhs, rhs

def add_final_state(m, q, n=None):
    if n is None:
        n = m.num_stores
    lhs = [machines.Store([q]), machines.Store([BLANK])] + [machines.Store()]*(n-2)
    rhs = [machines.Store([ACCEPT])] + [machines.Store()]*(n-1)
    m.add_transition(machines.Transition(lhs, rhs))

def get_final_states(m):
    final_states = set()
    if not m.has_input(1):
        return final_states
    for t in m.transitions:
        if list(t.rhs[0]) == [ACCEPT]:
            if len(t.lhs[0]) == 1 and list(t.lhs[1]) == [BLANK]:
                final_states.add(t.lhs[0][0])
    return final_states

