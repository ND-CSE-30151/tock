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

def zero_pad(n, i):
    return str(i).zfill(len(str(n)))

def convert_regexp(s, start=0):
    s = formats.dotstring(" "*start + s)
    s.i = start
    m = machines.Machine()
    m.num_stores = 2
    initial, finals = parse_union(s, m)
    formats.set_initial_state(m, initial)
    for q in finals:
        formats.add_final_state(m, q)
    return m

def parse_union(s, m):
    i = s.i
    initial, finals = parse_concat(s, m)
    if s.i < len(s) and s.c == '|':
        # There can never be more than one star with the same starting index,
        # so use the starting index for the extra state. It is possible
        # for a star and union to start at the same place (a*|b) so
        # union gets the earlier letter in the alphabet.
        new_initial = zero_pad(len(s), i) + "a"
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
    i = s.i
    initial, finals = parse_base(s, m)
    if s.i < len(s) and s.c == '*':
        parse_character(s, '*')
        # There can never be more than one star with the same starting index,
        # so use the starting index for the extra state. It is possible
        # for a star and union to start at the same place (a*|b) so
        # union gets the earlier letter in the alphabet.
        new_initial = zero_pad(len(s), i) + "i"
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
    elif s.i == len(s) or s.c in ')|':
        # Borrow the index of the following character,
        # which can never be a symbol.
        q = zero_pad(len(s), s.i)
        return q, [q]
    elif s.i < len(s) and s.c == '&':
        q = zero_pad(len(s), s.i)
        parse_character(s, '&')
        return q, [q]
    elif s.i < len(s):
        if s.c in '*|()':
            raise ValueError("expected symbol, found %s" % s.c)
        child = s.c
        q = zero_pad(len(s), s.i) + "s"
        r = zero_pad(len(s), s.i) + "t"
        m.add_transition(make_transition(q, s.c, r))
        s.i += 1
        return q, [r]
    else:
        assert False

if __name__ == "__main__":
    import sys
    print convert_regexp(sys.argv[1])
