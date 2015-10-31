import machines
import formats

__all__ = ['convert_regexp']

# Currently, symbols are single characters and whitespace is significant.

def make_transition(q, a, r):
    return machines.Transition((machines.Store([q]), machines.Store([a])),
                               (machines.Store([r]), machines.Store()))
def make_empty_transition(q, r):
    return machines.Transition((machines.Store([q]), machines.Store()),
                               (machines.Store([r]), machines.Store()))

def parse_character(s, c):
    if s.i == len(s):
        raise ValueError("expected %s, found end of string" % c)
    elif s.c != c:
        raise ValueError("expected %s, found %s" % (c, s.c))
    s.i += 1

def convert_regexp(s):
    s = formats.dotstring(s)
    m = machines.Machine()
    initial, finals = parse_union(s, m)
    formats.set_initial_state(m, initial)
    for q in finals:
        formats.add_final_state(m, q)
    return m

def parse_union(s, m):
    initial, finals = parse_concat(s, m)
    if s.i < len(s) and s.c == '|':
        new_initial = initial+"u"
        m.add_transition(make_empty_transition(new_initial, initial))

        while s.i < len(s) and s.c == '|':
            parse_character(s, '|')
            initial1, finals1 = parse_concat(s, m)
            m.add_transition(make_empty_transition(new_initial, initial1))
            finals += finals1

        initial = new_initial

    return initial, finals

def parse_concat(s, m):
    initial, finals = parse_star(s, m)
    while s.i < len(s) and s.c not in '|)':
        initial1, finals1 = parse_star(s, m)
        for qf in finals:
            m.add_transition(make_empty_transition(qf, initial1))
        finals = finals1
    return initial, finals

def parse_star(s, m):
    initial, finals = parse_base(s, m)
    if s.i < len(s) and s.c == '*':
        parse_character(s, '*')
        new_initial = initial+"s"
        m.add_transition(make_empty_transition(new_initial, initial))
        for qf in finals:
            m.add_transition(make_empty_transition(qf, initial))
        initial = new_initial
        finals += [new_initial]
    return initial, finals

def parse_base(s, m):
    if s.i < len(s) and s.c == '(':
        parse_character(s, '(')
        initial, final = parse_union(s, m)
        parse_character(s, ')')
        return initial, final
    elif s.i < len(s):
        if s.c in '*|()':
            raise ValueError("expected symbol, found %s" % s.c)
        child = s.c
        q = "q%s" % (s.i+1)
        r = "r%s" % (s.i+1)
        m.add_transition(make_transition(q, s.c, r))
        s.i += 1
        return q, [r]
    else:
        q = "e%s" % s.i
        return q, [q]

