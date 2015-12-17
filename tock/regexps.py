# coding=utf-8

from . import machines
from . import syntax
from . import graphs

__all__ = ['from_regexp', 'to_regexp']

def zero_pad(n, i):
    return str(i).zfill(len(str(n)))

def from_regexp(s, offset=0):
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

class Union(object):
    def __init__(self, args):
        self.args = tuple(args)
    def __str__(self):
        if len(self.args) == 0:
            return 'null'
        else:
            return '|'.join(map(str, self.args))
    def _repr_html_(self):
        if len(self.args) == 0:
            return '&empty;'
        else:
            return '|'.join(arg._repr_html_() for arg in self.args)

def union(args):
    newargs = []
    for arg in args:
        if isinstance(arg, Union):
            newargs.extend(arg.args)
        else:
            newargs.append(arg)
    if len(newargs) == 1:
        return newargs[0]
    else:
        return Union(newargs)

class Concatenation(object):
    def __init__(self, args):
        self.args = tuple(args)
    def __str__(self):
        if len(self.args) == 0:
            return '&'
        else:
            return ' '.join('({})'.format(arg) if isinstance(arg, Union) else str(arg) for arg in self.args)
    def _repr_html_(self):
        if len(self.args) == 0:
            return '&epsilon;'
        else:
            return ' '.join('({})'.format(arg._repr_html_()) if isinstance(arg, Union) else arg._repr_html_() for arg in self.args)

def concatenation(args):
    newargs = []
    for arg in args:
        if isinstance(arg, Union) and len(arg.args) == 0: # empty set
            return Union()
        if isinstance(arg, Concatenation):
            newargs.extend(arg.args)
        else:
            newargs.append(arg)
    if len(newargs) == 1:
        return newargs[0]
    else:
        return Concatenation(newargs)

class Star(object):
    def __init__(self, arg):
        self.arg = arg
    def __str__(self):
        if isinstance(self.arg, Symbol):
            return '{}*'.format(self.arg)
        else:
            return '({})*'.format(self.arg)
    def _repr_html_(self):
        if isinstance(self.arg, Symbol):
            return '{}*'.format(self.arg._repr_html_())
        else:
            return '({})*'.format(self.arg._repr_html_())

def star(arg):
    if isinstance(arg, (Union, Concatenation)) and len(arg.args) == 0:
        return Concatenation()
    else:
        return Star(arg)

class Symbol(object):
    def __init__(self, arg):
        self.arg = arg
    def __str__(self):
        return str(self.arg)
    def _repr_html_(self):
        return str(self)

def to_regexp(m, display_steps=False):
    if display_steps:
        from IPython.display import display, HTML

    if not m.is_finite():
        raise TypeError("machine must be a finite automaton")

    states = sorted(q for [q] in m.states)

    g = graphs.Graph({'rankdir': 'LR'})
    for t in m.get_transitions():
        [[lstate], read] = t.lhs
        [[rstate]] = t.rhs
        g.add_edge(lstate, rstate, {'label': concatenation(Symbol(x) for x in read)})

    # Add new start and accept nodes
    assert 'START' not in m.states
    g.add_node('START', {'start': True})
    g.add_edge('START', m.get_start_state(), {'label': concatenation([])})
    assert 'ACCEPT' not in m.states
    g.add_node('ACCEPT', {'accept': True})
    for q in m.get_accept_states():
        g.add_edge(q, 'ACCEPT', {'label': concatenation([])})

    if display_steps:
        display(g)

    while len(states) > 0:
        s = states.pop()
        display(HTML("eliminate " + s))
        for q in states + ['START']:
            for r in states + ['ACCEPT']:
                try:
                    inexpr = union(e['label'] for e in g.edges[q][s])
                    outexpr = union(e['label'] for e in g.edges[s][r])
                except KeyError:
                    continue
                if g.has_edge(s,s):
                    loopexpr = union(e['label'] for e in g.edges[s][s])
                    expr = concatenation([inexpr, star(loopexpr), outexpr])
                else:
                    expr = Concatenation([inexpr, outexpr])
                g.add_edge(q, r, {'label': expr})
        g.remove_node(s)

        if display_steps:
            display(g)

    if g.has_edge('START', 'ACCEPT'):
        return union(e['label'] for e in g.edges['START']['ACCEPT'])
    else:
        return union([])

