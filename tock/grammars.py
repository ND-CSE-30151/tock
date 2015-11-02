import machines
import formats

def zero_pad(n, i):
    return str(i).zfill(len(str(n)))

def convert_grammar(start, rules):
    """`rules` should be of the form [(a, [b, c]), ...]"""

    m = machines.Machine()
    m.num_stores = 3

    q1 = "%s.1" % zero_pad(len(rules)+1, 0)
    formats.set_initial_state(m, "start")
    formats.add_transition(m, 
                           (machines.Store(["start"]),
                            machines.Store(),
                            machines.Store()), 
                           (machines.Store([q1]),
                            machines.Store(["$"]),))
    formats.add_transition(m, 
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
            formats.add_transition(m, 
                                   (machines.Store(["loop"]),
                                    machines.Store(),
                                    machines.Store([lhs])), 
                                   (machines.Store(["loop"]),
                                    machines.Store([]),))
        else:
            q = "loop"
            for si, r in enumerate(rhs):
                if si < len(rhs)-1:
                    q1 = "%s.%s" % (zero_pad(len(rules)+1, ri+1), 
                                    zero_pad(len(rhs)+1, si+1))
                else:
                    q1 = "loop"
                formats.add_transition(m, 
                                       (machines.Store([q]),
                                        machines.Store(),
                                        machines.Store([lhs] if si==0 else [])), 
                                       (machines.Store([q1]),
                                        machines.Store([r]),))
                q = q1

    formats.add_transition(m, 
                           (machines.Store(["loop"]),
                            machines.Store(),
                            machines.Store(["$"])), 
                           (machines.Store(["accept"]),
                            machines.Store(),))
    formats.add_final_state(m, "accept")

    return m

if __name__ == "__main__":
    print convert_grammar("S", [("S", ["a", "T", "b"]),
                                ("S", ["b"]),
                                ("T", ["T", "a"]),
                                ("T", [])])
    
