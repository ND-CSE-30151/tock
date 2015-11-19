from . import machines
from . import syntax

__all__ = ['convert_regexp']

def zero_pad(n, i):
    return str(i).zfill(len(str(n)))

def convert_regexp(s, offset=0):
    s = syntax.lexer(s)
    s.offset = offset
    m = machines.Machine(2, state=0, input=1)
    initial, finals = parse_union(s, m)
    m.set_start_state(initial)
    for q in finals:
        m.add_accept_state(q)
    return m

def parse_union(s, m):
    i = s.pos
    initial, finals = parse_concat(s, m)
    if s.pos < len(s) and s.cur == '|':
        # There can never be more than one star with the same starting index,
        # so use the starting index for the extra state. It is possible
        # for a star and union to start at the same place (a*|b) so
        # union gets the earlier letter in the alphabet.
        new_initial = zero_pad(len(s), i) + "a"
        m.add_transition((new_initial, []), (initial,))

        while s.pos < len(s) and s.cur == '|':
            syntax.parse_character(s, '|')
            initial1, finals1 = parse_concat(s, m)
            m.add_transition((new_initial, []), (initial1,))
            finals += finals1

        initial = new_initial

    return initial, finals

def parse_concat(s, m):
    initial, finals = parse_star(s, m)
    while s.pos < len(s) and s.cur not in '|)':
        initial1, finals1 = parse_star(s, m)
        for qf in finals:
            m.add_transition((qf, []), (initial1,))
        finals = finals1
    return initial, finals

def parse_star(s, m):
    i = s.pos
    initial, finals = parse_base(s, m)
    if s.pos < len(s) and s.cur == '*':
        syntax.parse_character(s, '*')
        # There can never be more than one star with the same starting index,
        # so use the starting index for the extra state. It is possible
        # for a star and union to start at the same place (a*|b) so
        # union gets the earlier letter in the alphabet.
        new_initial = zero_pad(len(s), i) + "i"
        m.add_transition((new_initial, []), (initial,))
        for qf in finals:
            m.add_transition((qf, []), (initial,))
        initial = new_initial
        finals += [new_initial]
    return initial, finals

def parse_base(s, m):
    if s.pos < len(s) and s.cur == '(':
        syntax.parse_character(s, '(')
        initial, final = parse_union(s, m)
        syntax.parse_character(s, ')')
        return initial, final
    elif s.pos == len(s) or s.cur in ')|':
        raise ValueError("expected symbol, found nothing (use & for the empty string)")
        """# Borrow the index of the following character,
        # which can never be a symbol.
        q = zero_pad(len(s), s.pos)
        return q, [q]"""
    elif s.pos < len(s) and s.cur == '&':
        q = zero_pad(len(s)+s.offset, s.pos+s.offset)
        syntax.parse_character(s, '&')
        return q, [q]
    elif s.pos < len(s):
        q = zero_pad(len(s)+s.offset, s.pos+s.offset) + "s"
        r = zero_pad(len(s)+s.offset, s.pos+s.offset) + "t"
        a = syntax.parse_symbol(s)
        m.add_transition((q, a), (r,))
        return q, [r]
    else:
        assert False

if __name__ == "__main__":
    import sys
    print(convert_regexp(sys.argv[1]))
