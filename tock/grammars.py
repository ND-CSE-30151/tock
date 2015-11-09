from . import machines
from . import lexer
from . import special

def zero_pad(n, i):
    return str(i).zfill(len(str(n)))

def convert_grammar(rules):
    """Argument `rules` is a file-like object or sequence of strings.
       Each is of the form lhs -> rhs, where lhs is a nonterminal and
       rhs is a space-separated sequence of terminals or nonterminals.
       The lhs of the first rule is taken to be the start symbol."""

    parsed_rules = []
    for rule in rules:
        tokens = lexer.lexer(rule)
        lhs = lexer.parse_symbol(tokens)
        lexer.parse_character(tokens, '->')
        rhs = []
        if tokens.cur == '&':
            lexer.parse_character(tokens, '&')
            lexer.parse_end(tokens)
        else:
            while tokens.pos < len(tokens):
                rhs.append(lexer.parse_symbol(tokens))
        parsed_rules.append((lhs, rhs))
    rules = parsed_rules
    start = rules[0][0]

    m = machines.Machine()
    m.num_stores = 3

    q1 = "%s.1" % zero_pad(len(rules)+1, 0)
    special.set_initial_state(m, "start")
    special.add_transition(m, 
                           (machines.Store(["start"]),
                            machines.Store(),
                            machines.Store()), 
                           (machines.Store([q1]),
                            machines.Store(["$"]),))
    special.add_transition(m, 
                           (machines.Store([q1]),
                            machines.Store(),
                            machines.Store()), 
                           (machines.Store(["loop"]),
                            machines.Store([start]),))

    nonterminals = set([start])
    symbols = set()
    for ri, (lhs, rhs) in enumerate(rules):
        nonterminals.add(lhs)
        symbols.add(lhs)
        symbols.update(rhs)
        if len(rhs) == 0:
            special.add_transition(m, 
                                   (machines.Store(["loop"]),
                                    machines.Store(),
                                    machines.Store([lhs])), 
                                   (machines.Store(["loop"]),
                                    machines.Store([])))
        else:
            q = "loop"
            for si, r in reversed(list(enumerate(rhs))):
                if si > 0:
                    q1 = "%s.%s" % (zero_pad(len(rules)+1, ri+1), 
                                    zero_pad(len(rhs)+1, si))
                else:
                    q1 = "loop"
                special.add_transition(m, 
                                       (machines.Store([q]),
                                        machines.Store(),
                                        machines.Store([lhs] if si==len(rhs)-1 else [])), 
                                       (machines.Store([q1]),
                                        machines.Store([r])))
                q = q1

    special.add_transition(m, 
                           (machines.Store(["loop"]),
                            machines.Store(),
                            machines.Store(["$"])), 
                           (machines.Store(["accept"]),
                            machines.Store()))
    special.add_final_state(m, "accept")

    for a in symbols - nonterminals:
        special.add_transition(m,
                               (machines.Store(["loop"]),
                                machines.Store([a]),
                                machines.Store([a])),
                               (machines.Store(["loop"]),
                                machines.Store()))
                                
    return m
