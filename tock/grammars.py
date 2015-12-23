from . import machines
from . import syntax

__all__ = ['from_grammar']

def zero_pad(n, i):
    return str(i).zfill(len(str(n)))

def from_grammar(rules):
    """Argument `rules` is a file-like object or sequence of strings.
       Each is of the form lhs -> rhs, where lhs is a nonterminal and
       rhs is a space-separated sequence of terminals or nonterminals.
       The lhs of the first rule is taken to be the start symbol."""

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
    rules = parsed_rules
    start = rules[0][0]

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

def to_grammar(m):
    if not m.is_pushdown():
        raise TypeError("only pushdown automata can be converted to (context-free) grammars")

    states = set()
    transitions = []
    stack_alphabet = set()
    for t in m.get_transitions():
        ([q], a, x) = t.lhs
        ([r], y) = t.rhs
        states.add(q)
        states.add(r)
        if len(a) > 1 or len(x) > 1 or len(y) > y:
            raise NotSupportedException("multiple symbols in transition not supported")
        stack_alphabet |= x
        stack_alphabet |= y
        transitions.append((q, a, x, r, y))

    # Automaton should have the following properties:
    # - no multiple symbols
    # - no pop+push rules
    # - empties stack at end
    # - single accept state

    # Create new accept state and hallucinate empty transitions from
    # real accept states to it.
    accept_state = "accept"
    start_var = (m.get_start_state(), accept_state)

    # For each p, q, r, s \in Q, u \in \Gamma, and a, b \in \Sigma_\epsilon,
    # if \delta(p, a, \epsilon) contains (r, u) and \delta(s, b, u) contains
    # (q, \epsilon), put the rule A_{pq} -> a A_{rs} b in G.

    # For each p, q, r \in Q, put the rule A_{pq} -> A_{pr} A_{rq} in G.
    for p in m.states:
        for q in m.states:
            for r in m.states:
                rules.append(((p,q), [(p,r), (r,q)]))

    # For each p \in Q, put the rule A_{pp} -> \epsilon in G
    for p in m.states:
        rules.append(((p,p), []))

    return rules
