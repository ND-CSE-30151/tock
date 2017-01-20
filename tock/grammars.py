import collections
from . import machines
from . import syntax

__all__ = ['from_grammar', 'to_grammar']

class Grammar(object):
    def __init__(self, start):
        self.start = start
        self.rules = []

    def add_rule(self, lhs, rhs):
        self.rules.append((machines.Store(lhs, None), machines.Store(rhs, None)))

    def __str__(self):
        result = []
        result.append('start: {}'.format(self.start))
        for lhs, rhs in self.rules:
            result.append('{} -> {}'.format(lhs, rhs))
        return '\n'.join(result)

    def _repr_html_(self):
        result = []
        if hasattr(self.start, '_repr_html_'):
            result.append('start: {}'.format(self.start._repr_html_()))
        else:
            result.append('start: {}'.format(self.start))
        for lhs, rhs in self.rules:
            result.append('{} &rarr; {}'.format(lhs._repr_html_(), rhs._repr_html_()))
        return '<br>\n'.join(result)

def zero_pad(n, i):
    return str(i).zfill(len(str(n)))

def fresh(s, alphabet):
    while s in alphabet:
        s += "'"
    return s

def from_grammar(rules, method="topdown"):
    """Argument `rules` is a file-like object or sequence of strings.
       Each is of the form lhs -> rhs, where lhs is a nonterminal and
       rhs is a space-separated sequence of terminals or nonterminals.
       The lhs of the first rule is taken to be the start symbol."""
    if method == "topdown":
        return from_grammar_topdown(rules)
    else:
        raise ValueError("unknown method '{}'".format(method))

def _read_rules(rules):
    parsed_rules = []
    for rule in rules:
        tokens = syntax.lexer(rule)
        lhs = syntax.parse_symbol(tokens)
        syntax.parse_character(tokens, '->')
        rhs = []
        if tokens.cur == '&':
            syntax.parse_character(tokens, '&')
            syntax.parse_end(tokens)
        else:
            while tokens.pos < len(tokens):
                rhs.append(syntax.parse_symbol(tokens))
        parsed_rules.append((lhs, rhs))
    return parsed_rules, parsed_rules[0][0]

def from_grammar_topdown(rules):
    """Argument `rules` is a file-like object or sequence of strings.
       Each is of the form lhs -> rhs, where lhs is a nonterminal and
       rhs is a space-separated sequence of terminals or nonterminals.
       The lhs of the first rule is taken to be the start symbol."""

    rules, start = _read_rules(rules)

    m = machines.PushdownAutomaton()

    q1 = "%s.1" % zero_pad(len(rules)+1, 0)
    m.set_start_state("start")
    m.add_transition(("start", [], []), (q1,     "$"))
    m.add_transition((q1,      [], []), ("loop", start))

    nonterminals = set([start])
    symbols = set()
    for ri, (lhs, rhs) in enumerate(rules):
        nonterminals.add(lhs)
        symbols.add(lhs)
        symbols.update(rhs)
        if len(rhs) == 0:
            m.add_transition(("loop", [], lhs), ("loop", []))

        else:
            q = "loop"
            for si, r in reversed(list(enumerate(rhs))):
                if si > 0:
                    q1 = "%s.%s" % (zero_pad(len(rules)+1, ri+1), 
                                    zero_pad(len(rhs)+1, si))
                else:
                    q1 = "loop"
                m.add_transition((q, [], lhs if si==len(rhs)-1 else []),
                                 (q1, r))

                q = q1

    m.add_transition(("loop", [], "$"), ("accept", []))
    m.add_accept_state("accept")

    for a in symbols - nonterminals:
        m.add_transition(("loop", a, a), ("loop", []))
                                
    return m

class Tuple(tuple):
    def __str__(self):
        return '('+','.join(map(str, self))+')'
    def _repr_html_(self):
        return '(' + ','.join(x._repr_html_() if hasattr(x, '_repr_html_') else str(x) for x in self) + ')'

def to_grammar(m):
    if not m.is_pushdown():
        raise TypeError("only pushdown automata can be converted to (context-free) grammars")

    push = collections.defaultdict(list)
    pop = collections.defaultdict(list)
    stack_alphabet = set()
    for t in m.get_transitions():
        ([q], a, x) = t.lhs
        ([r], y) = t.rhs
        stack_alphabet.update(x)
        stack_alphabet.update(y)
        if len(x) > 1 or len(y) > 1:
            raise NotImplementedError("multiple pushes/pops not supported")
        if len(x) == 0 and len(y) == 1:
            push[y[0]].append((q, a, x, r, y))
        elif len(x) == 1 and len(y) == 0:
            pop[x[0]].append((q, a, x, r, y))
        else:
            raise NotImplementedError("transitions must either push or pop but not both")

    start = fresh('start', m.states)
    bottom = fresh('$', stack_alphabet)
    push[bottom].append((start, [], [], m.get_start_state(), [bottom]))

    # Make automaton empty its stack before accepting
    accept = fresh('accept', m.states)
    empty = fresh('empty', m.states)
    for x in stack_alphabet:
        for q in m.get_accept_states():
            pop[x].append((q, [], [x], empty, []))
        pop[x].append((empty, [], [x], empty, []))
    for q in m.get_accept_states():
        pop[bottom].append((q, [], [bottom], accept, []))
    pop[bottom].append((empty, [], [bottom], accept, []))

    g = Grammar(Tuple((start, accept)))

    # For each p, q, r, s \in Q, u \in \Gamma, and a, b \in \Sigma_\epsilon,
    # if \delta(p, a, \epsilon) contains (r, u) and \delta(s, b, u) contains
    # (q, \epsilon), put the rule A_{pq} -> a A_{rs} b in G.
    for u in stack_alphabet:
        for p, a, _, r, _ in push[u]:
            for s, b, _, q, _ in pop[u]:
                g.add_rule([Tuple((p,q))], list(a) + [Tuple((r,s))] + list(b))

    # For each p, q, r \in Q, put the rule A_{pq} -> A_{pr} A_{rq} in G.
    for p in m.states:
        for q in m.states:
            for r in m.states:
                g.add_rule([Tuple((p,q))], [Tuple((p,r)), Tuple((r,q))])

    # For each p \in Q, put the rule A_{pp} -> \epsilon in G
    for p in m.states:
        g.add_rule([Tuple((p,p))], [])

    return g
