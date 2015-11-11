from . import machines
from . import syntax

def zero_pad(n, i):
    return str(i).zfill(len(str(n)))

def convert_grammar(rules):
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

    m = machines.Machine(3, input=1)

    q1 = "%s.1" % zero_pad(len(rules)+1, 0)
    m.set_start_config(("start", [], []))
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
    m.add_accept_config(["accept", syntax.BLANK, []])

    for a in symbols - nonterminals:
        m.add_transition(("loop", a, a), ("loop", []))
                                
    return m
