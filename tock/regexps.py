# coding=utf-8

from . import machines
from . import syntax
from . import graphs
import six

__all__ = ['from_regexp', 'to_regexp', 'string_to_regexp']

### Regular expression objects

class RegularExpression(object):
    def __init__(self, op, args, start=None, end=None):
        self.op = op
        self.args = tuple(args)
        self.start = start
        self.end = end

    def __str__(self, format='ascii'):
        if self.op == 'union':
            if len(self.args) > 0:
                return '|'.join(arg.__str__(format=format) for arg in self.args)
            else:
                return '&empty;' if format == 'html' else '{}'

        elif self.op == 'concatenation':
            if len(self.args) > 0:
                args = []
                for arg in self.args:
                    s = arg.__str__(format=format)
                    if arg.op == 'union':
                        s = '('+s+')'
                    args.append(s)
                return ' '.join(args)
            else:
                return '&epsilon;' if format == 'html' else '&'

        elif self.op == 'star':
            [arg] = self.args
            s = arg.__str__(format=format)
            if arg.op != 'symbol':
                s = '('+s+')'
            return s+'*'

        elif self.op == 'symbol':
            [arg] = self.args
            if format == 'html' and hasattr(arg, '_repr_html_'):
                return arg._repr_html_()
            else:
                return str(arg)

    def _repr_html_(self):
        return self.__str__(format='html')

def union(args):
    newargs = []
    for arg in args:
        if arg.op == 'union':
            newargs.extend(arg.args)
        else:
            newargs.append(arg)
    if len(newargs) == 1:
        return newargs[0]
    else:
        return RegularExpression('union', newargs)

def concatenation(args):
    newargs = []
    for arg in args:
        if arg.op == 'union' and len(arg.args) == 0: # empty set
            return union([])
        elif arg.op == 'concatenation':
            newargs.extend(arg.args)
        else:
            newargs.append(arg)
    if len(newargs) == 1:
        return newargs[0]
    else:
        return RegularExpression('concatenation', newargs)

def star(arg):
    if arg in ['union', 'concatenation'] and len(arg.args) == 0:
        return concatenation([])
    else:
        return RegularExpression('star', [arg])

def symbol(arg):
    return RegularExpression('symbol', [arg])

### Parser for regular expressions

def string_to_regexp(s):
    """Converts a string to a regular expression.

    Regular expressions allow the following operations:
    - Symbols
    - Empty string (&)
    - Union (|)
    - Concatenation: Two concatenated symbols must be separated by a
      space. For example, "a b" is "a" concatenated with "b", but "ab"
      is a single symbol.
    - Kleene star (*)
    """
    s = syntax.lexer(s)
    r = parse_union(s)
    if s.pos < len(s):
        raise ValueError("unexpected characters {} after regular expression".format(s[s.pos:]))
    return r

def parse_union(s):
    i = s.pos
    args = [parse_concatenation(s)]
    while s.pos < len(s) and s.cur == '|':
        syntax.parse_character(s, '|')
        args.append(parse_concatenation(s))
    return union(args)

def parse_concatenation(s):
    args = [parse_star(s)]
    while s.pos < len(s) and s.cur not in '|)':
        args.append(parse_star(s))
    return concatenation(args)

def parse_star(s):
    i = s.pos
    arg = parse_base(s)
    if s.pos < len(s) and s.cur == '*':
        syntax.parse_character(s, '*')
        return star(arg)
    else:
        return arg

def parse_base(s):
    if s.pos < len(s) and s.cur == '(':
        syntax.parse_character(s, '(')
        e = parse_union(s)
        syntax.parse_character(s, ')')
        return e
    elif s.pos == len(s) or s.cur in ')|':
        raise ValueError("expected symbol, found nothing (use & for the empty string)")
    elif s.pos < len(s) and s.cur == '&':
        syntax.parse_character(s, '&')
        return concatenation([])
    elif s.pos < len(s):
        a = syntax.parse_symbol(s)
        return symbol(a)
    else:
        assert False

def from_regexp(e, display_steps=False):
    """Convert a regular expression to a NFA.

    display_steps: if True and if run inside a Jupyter notebook,
    displays all steps of the conversion.
    """
    def count(e):
        """Predetermine number of states we will need."""
        if e.op == 'union':
            return 1+sum(count(arg) for arg in e.args)
        elif e.op == 'concatenation':
            return sum(count(arg) for arg in e.args)
        elif e.op == 'star':
            return 1+count(e.args[0])
        elif e.op == 'symbol':
            return 2

    def zero_pad(i):
        return str(i).zfill(len(str(num_states)))

    def visit(e, i):
        m = machines.FiniteAutomaton()

        if e.op == 'symbol':
            start = "q" + zero_pad(i)
            accept = "q" + zero_pad(i+1)
            i += 2
            m.set_start_state(start)
            m.add_accept_state(accept)
            m.add_transition((start, e.args[0]), (accept,))

        elif e.op == 'concatenation' and len(e.args) == 0: # empty string
            start = "q" + zero_pad(i)
            i += 1
            m.set_start_state(start)
            m.add_accept_state(start)

        else:
            margs = []
            for arg in e.args:
                marg, i = visit(arg, i)
                m.transitions.extend(marg.transitions)
                margs.append(marg)

            if e.op == 'union':
                start = "q" + zero_pad(i)
                i += 1
                m.set_start_state(start)
                for marg in margs:
                    m.add_transition((start, []), (marg.get_start_state(),))
                    for q in marg.get_accept_states():
                        m.add_accept_state(q)

            elif e.op == 'concatenation':
                m.set_start_state(margs[0].get_start_state())
                for j in range(len(margs)-1):
                    for q in margs[j].get_accept_states():
                        m.add_transition((q, []), (margs[j+1].get_start_state(),))
                for q in margs[-1].get_accept_states():
                    m.add_accept_state(q)

            elif e.op == 'star':
                start = "q" + zero_pad(i)
                i += 1
                m.set_start_state(start)
                m.add_accept_state(start)
                start1 = margs[0].get_start_state()
                m.add_transition((start, []), (start1,))
                for q in margs[0].get_accept_states():
                    m.add_transition((q, []), (start1,))
                    m.add_accept_state(q)

            else:
                assert False

        if display_steps:
            display(HTML('subexpression: '+e._repr_html_()))
            display(m)

        return m, i

    if display_steps:
        from IPython.display import display, HTML
    if isinstance(e, six.string_types):
        e = string_to_regexp(e)
    num_states = count(e)
    m, _ = visit(e, 1)
    return m

def fresh(s, alphabet):
    while s in alphabet:
        s += "'"
    return s

def to_regexp(m, display_steps=False):
    """Convert a finite automaton to a regular expression.

    display_steps: if True and if run inside a Jupyter notebook,
    displays all steps of the conversion."""
    def union_edge(q, r, e):
        if g.has_edge(q, r):
            g[q][r][0]['label'] = union([g[q][r][0]['label'], e])
        else:
            g.add_edge(q, r, {'label': e})

    if display_steps:
        from IPython.display import display, HTML

    if not m.is_finite():
        raise TypeError("machine must be a finite automaton")

    states = sorted(m.states)

    g = graphs.Graph({'rankdir': 'LR'})
    for t in m.get_transitions():
        [[lstate], read] = t.lhs
        [[rstate]] = t.rhs
        union_edge(lstate, rstate, concatenation(symbol(x) for x in read))

    # Add new start and accept nodes
    start = fresh('start', m.states)
    g.add_node(start, {'start': True})
    g.add_edge(start, m.get_start_state(), {'label': concatenation([])})
    accept = fresh('accept', m.states)
    g.add_node(accept, {'accept': True})
    for q in m.get_accept_states():
        g.add_edge(q, accept, {'label': concatenation([])})

    if display_steps:
        display(g)

    while len(states) > 0:
        s = states.pop()
        if display_steps:
            display(HTML("eliminate " + s))
        for q in states + [start]:
            for r in states + [accept]:
                try:
                    inexpr = union(e['label'] for e in g.edges[q][s])
                    outexpr = union(e['label'] for e in g.edges[s][r])
                except KeyError:
                    continue
                if g.has_edge(s,s):
                    loopexpr = union(e['label'] for e in g.edges[s][s])
                    expr = concatenation([inexpr, star(loopexpr), outexpr])
                else:
                    expr = concatenation([inexpr, outexpr])
                union_edge(q, r, expr)
        g.remove_node(s)

        if display_steps:
            display(g)

    if g.has_edge(start, accept):
        return g.edges[start][accept][0]['label']
    else:
        return union([])

