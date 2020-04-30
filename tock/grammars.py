import collections
import dataclasses
from . import machines
from . import syntax
from . import operations

__all__ = ['Grammar', 'from_grammar', 'to_grammar']

class Grammar:
    """A string-rewriting grammar."""
    def __init__(self):
        self.nonterminals = set()
        self.start_nonterminal = None
        self.rules = []

    @classmethod
    def from_file(cls, filename):
        """Read a grammar from a file.

        Arguments:
            filename (str): name of file to read from
        Returns:
            Grammar: a CFG

        The file should contain one rule per line, for example::

            S -> a S b
            S -> &

        Currently the grammar must be a context-free grammar. The
        nonterminal symbols are exactly those that appear on a
        left-hand side. The left-hand side of the first rule is the
        start symbol.
        """
        with open(filename) as f:
            return cls.from_lines(f)
        
    @classmethod
    def from_lines(cls, lines):
        """Read a grammar from a list of strings (see `from_file`).

        Arguments:
            lines: a list of strings
        Returns:
            Grammar: a CFG
        """
        g = cls()
        parsed_rules = []
        first = True
        for line in lines:
            tokens = syntax.lexer(line)
            lhs = syntax.parse_symbol(tokens)
            g.nonterminals.add(lhs)
            if first:
                g.set_start_nonterminal(lhs)
                first = False
            syntax.parse_character(tokens, syntax.ARROW)
            rhs = []
            if tokens.cur == syntax.EPSILON:
                syntax.parse_character(tokens, syntax.EPSILON)
                syntax.parse_end(tokens)
            else:
                while tokens.pos < len(tokens):
                    rhs.append(syntax.parse_symbol(tokens))
            g.add_rule(lhs, rhs)
        return g

    def set_start_nonterminal(self, x):
        """Set the start symbol to `x`. If `x` is not already a nonterminal,
        it is added to the nonterminal alphabet."""
        self.add_nonterminal(x)
        self.start_nonterminal = x

    def add_nonterminal(self, x):
        """Add `x` to the nonterminal alphabet."""
        self.nonterminals.add(x)
        
    def add_rule(self, lhs, rhs):
        """Add rule with left-hand side `lhs` and right-hand side `rhs`,
        where `lhs` and `rhs` are both Strings.
        """
        self.rules.append((syntax.String(lhs), syntax.String(rhs)))

    def __str__(self):
        result = []
        result.append('nonterminals: {{{}}}'.format(','.join(map(str, sorted(self.nonterminals)))))
        result.append('start: {}'.format(self.start_nonterminal))
        for lhs, rhs in self.rules:
            result.append('{} → {}'.format(lhs, rhs))
        return '\n'.join(result)

    def _repr_html_(self):
        result = []
        result.append("nonterminals: {{{}}}".format(','.join(x._repr_html_() for x in sorted(self.nonterminals))))
        result.append('start: {}'.format(self.start_nonterminal._repr_html_()))
        for lhs, rhs in self.rules:
            result.append('{} &rarr; {}'.format(lhs._repr_html_(), rhs._repr_html_()))
        return '<br>\n'.join(result)

    def is_unrestricted(self):
        return True

    def has_strict_start(self):
        """Returns True iff the start nonterminal does not appear in the rhs
        of any rule. I don't know what the correct terminology for
        this is.
        """
        for _, rhs in self.rules:
            if self.start_nonterminal in rhs:
                return False
        return True

    def is_noncontracting(self):
        """Returns True iff the grammar is *essentially* noncontracting, that
        is, each rule is of the form α → β where one of the following is true:
        
        - len(β) ≥ len(α)
        - α = S, β = ε, and S does not occur on the rhs of any rule

        """
        for lhs, rhs in self.rules:
            if (len(lhs) == 1 and lhs[0] == self.start_nonterminal and
                len(rhs) == 0 and self.has_strict_start()):
                continue
            if len(rhs) < len(lhs):
                return False
        return True

    def is_contextsensitive(self):
        """Returns True iff the grammar is context-sensitive, that is, each
        rule is of the form α A β → α B β where one of the following is true:

        - A is a nonterminal and len(B) > 0
        - A = S, α = β = B = ε, and S does not occur on the rhs of any rule
        """
        if not self.is_noncontracting():
            return False
        for lhs, rhs in self.rules:
            if (len(lhs) == 1 and lhs[0] == self.start_nonterminal and
                len(rhs) == 0 and self.has_strict_start()):
                continue
            for li, lx in enumerate(lhs):
                suffix = len(lhs)-li-1
                if (lx in self.nonterminals and lhs[:li] == rhs[:li] and
                    (suffix == 0 or lhs[-suffix:] == rhs[-suffix:])):
                    break
            else:
                return False
        return True

    def is_contextfree(self):
        """Returns True iff the grammar is context-free."""
        for lhs, rhs in self.rules:
            if len(lhs) != 1:
                print(repr(lhs), len(lhs))
                return False
            if lhs[0] not in self.nonterminals:
                print(repr(lhs), repr(rhs), repr(self.nonterminals))
                return False
        return True

    def is_leftlinear(self):
        """Returns True iff the grammar is left-linear, that is, it is context-free and
        every rule is of the form A → B w or A → w where w contains only terminals.
        """
        if not self.is_contextfree():
            return False
        for _, rhs in self.rules:
            if any(x in self.nonterminals for x in rhs[1:]):
                return False
        return True
            
    def is_rightlinear(self):
        """Returns True iff the grammar is left-linear, that is, it is context-free and
        every rule is of the form A → w B or A → w where w contains only terminals.
        """
        if not self.is_contextfree():
            return False
        for _, rhs in self.rules:
            if any(x in self.nonterminals for x in rhs[:-1]):
                return False
        return True

    def remove_useless(self):
        """Returns a new grammar containing just useful rules."""
        if not self.is_contextfree():
            raise ValueError("grammar must be context-free")
        by_lhs = collections.defaultdict(list)
        by_rhs = collections.defaultdict(list)
        for [lhs], rhs in self.rules:
            by_lhs[lhs].append((lhs, rhs))
            for y in rhs:
                if y in self.nonterminals:
                    by_rhs[y].append((lhs, rhs))
            
        agenda = collections.deque([self.start_nonterminal])
        reachable = set()
        while len(agenda) > 0:
            x = agenda.popleft()
            if x in reachable: continue
            reachable.add(x)
            for _, rhs in by_lhs[x]:
                for y in rhs:
                    if y in by_lhs:
                        agenda.append(y)

        agenda = collections.deque()
        productive = set()
        for [lhs], rhs in self.rules:
            if all(y not in self.nonterminals for y in rhs):
                agenda.append(lhs)
        while len(agenda) > 0:
            y = agenda.popleft()
            if y in productive: continue
            productive.add(y)
            for lhs, rhs in by_rhs[y]:
                if all(y not in self.nonterminals or y in productive for y in rhs):
                    agenda.append(lhs)

        g = Grammar()
        g.set_start_nonterminal(self.start_nonterminal)

        for [lhs], rhs in self.rules:
            if (lhs in reachable & productive and
                all(y not in self.nonterminals or y in reachable & productive for y in rhs)):
                g.add_rule([lhs], rhs)
        return g

    def compute_nullable(self):
        """Compute, for every nonterminal and rhs suffix α,
        whether α ⇒* ε.
        """
        if not self.is_contextfree():
            raise ValueError("grammar must be context-free")
        nullable = {syntax.String()}
        prev_size = None
        while len(nullable) != prev_size:
            prev_size = len(nullable)
            for lhs, rhs in self.rules:
                for i in reversed(range(len(rhs))):
                    if rhs[i+1:] in nullable and rhs[i:i+1] in nullable:
                        nullable.add(rhs[i:])
                if rhs in nullable:
                    nullable.add(lhs)
        return nullable

    def compute_first(self, nullable=None):
        """Compute, for every terminal, nonterminal, and rhs suffix α, the set of
        terminals b where α ⇒* b γ for some γ.
        """
        if not self.is_contextfree():
            raise ValueError("grammar must be context-free")
        if nullable is None:
            nullable = self.compute_nullable()
        first = {syntax.String(): set()}
        for lhs, rhs in self.rules:
            first.setdefault(lhs, set())
            for i in range(len(rhs)):
                if rhs[i] not in self.nonterminals:
                    first.setdefault(rhs[i:i+1], {rhs[i]})
                first.setdefault(rhs[i:], set())

        changed = True
        def update(s, x):
            nonlocal changed
            n = len(s)
            s.update(x)
            if n != len(s):
                changed = True
                    
        while changed:
            changed = False
            for lhs, rhs in self.rules:
                for i in reversed(range(len(rhs))):
                    update(first[rhs[i:]], first[rhs[i:i+1]])
                    if rhs[i:i+1] in nullable:
                        update(first[rhs[i:]], first[rhs[i+1:]])
                update(first[lhs], first[rhs])

        return first

    def compute_follow(self, nullable=None, first=None):
        """Compute, for every nonterminal A, the set of terminals b where 
        S →* γ A b δ for some γ, δ."""
        if not self.is_contextfree():
            raise ValueError("grammar must be context-free")
        if nullable is None:
            nullable = self.compute_nullable()
        if first is None:
            first = self.compute_first(nullable)

        follow = {x: set() for x in self.nonterminals}
        follow[self.start_nonterminal].add('⊣')
        
        changed = True
        def update(s, x):
            nonlocal changed
            n = len(s)
            s.update(x)
            if n != len(s):
                changed = True
                    
        while changed:
            changed = False
            for [lhs], rhs in self.rules:
                for i in range(len(rhs)):
                    if rhs[i] in self.nonterminals:
                        update(follow[rhs[i]], first[rhs[i+1:]])
                        if rhs[i+1:] in nullable:
                            update(follow[rhs[i]], follow[lhs])
        return follow
                
def zero_pad(n, i):
    return str(i).zfill(len(str(n)))

def fresh(s, alphabet):
    while s in alphabet:
        s += "'"
    return s

def from_grammar(g, mode="topdown"):
    """Convert a CFG to a PDA.

    Arguments:
        g (Grammar): the grammar to convert, which must be a CFG.
        mode (str): selects which algorithm to use. Possible values are:

          - ``"topdown"``: nondeterministic top-down, as in Sipser (3e) Lemma 2.21.
          - ``"bottomup"``: nondeterministic bottom-up.
          - ``"ll1"``: LL(1) deterministic top-down.
          - ``"lr0"``: LR(0) deterministic bottom-up.

    Returns:
        Machine: a PDA equivalent to `g`.
    """

    if g.is_contextfree():
        if mode == "topdown":
            return from_cfg_topdown(g)
        if mode == "ll1":
            return from_cfg_ll1(g)
        elif mode == "bottomup":
            return from_cfg_bottomup(g)
        if mode == "lr0":
            return from_cfg_lr0(g)
        else:
            raise ValueError("unknown mode '{}'".format(mode))
    else:
        raise NotImplementedError()

def from_cfg_topdown(g):
    m = machines.PushdownAutomaton()

    m.set_start_state('start')
    m.add_transition(('start', [], []), ('loop', [g.start_nonterminal, '$']))

    terminals = set()
    for [[lhs], rhs] in g.rules:
        for x in rhs:
            if x not in g.nonterminals:
                terminals.add(x)
        m.add_transition(('loop', [], lhs), ('loop', rhs))

    m.add_transition(("loop", [], "$"), ("accept", []))
    for a in terminals:
        m.add_transition(("loop", a, a), ("loop", []))
    m.add_accept_state("accept")
                                
    return m

END = syntax.Symbol('-|')

def from_cfg_ll1(g):
    nullable = g.compute_nullable()
    first = g.compute_first(nullable)
    follow = g.compute_follow(nullable, first)
    
    m = machines.PushdownAutomaton()

    m.set_start_state('start')
    m.add_transition(('start', [], []), ('loop', [g.start_nonterminal, '$']))

    terminals = set()
    for [_, rhs] in g.rules:
        for x in rhs:
            if x not in g.nonterminals:
                terminals.add(x)
                
    for [[lhs], rhs] in g.rules:
        for c in terminals | {END}:
            if c in first[rhs] or (rhs in nullable and c in follow[lhs]):
                m.add_transition((c, [], lhs), (c, rhs))
    for a in terminals:
        m.add_transition(('loop', a, []), (a, []))
        m.add_transition((a, [], a), ('loop', []))
    m.add_transition(('loop', '_', []), (END, [])) # treat blank as endmarker
    m.add_transition((END, [], '$'), ('accept', []))
    m.add_accept_state("accept")
                                
    return m

def from_cfg_bottomup(g):
    m = machines.PushdownAutomaton()

    m.set_start_state('start')
    m.add_transition(('start', [], []), ('loop', ['$']))

    terminals = set()
    for [[lhs], rhs] in g.rules:
        for x in rhs:
            if x not in g.nonterminals:
                terminals.add(x)
        m.add_transition(("loop", [], reversed(rhs)), ("loop", lhs))

    m.add_transition(("loop", [], [g.start_nonterminal, '$']), ("accept", []))
    for a in terminals:
        m.add_transition(("loop", a, []), ("loop", a))
    m.add_accept_state("accept")
                                
    return m

@dataclasses.dataclass(frozen=True, order=True)
class DottedRule:
    top: bool
    lhs: syntax.Symbol
    rhs: tuple
    dot: int

    def __init__(self, lhs, rhs, dot):
        if lhs is None:
            object.__setattr__(self, 'top', True)
            object.__setattr__(self, 'lhs', None)
        else:
            object.__setattr__(self, 'top', False)
            object.__setattr__(self, 'lhs', lhs)
        object.__setattr__(self, 'rhs', tuple(rhs))
        object.__setattr__(self, 'dot', dot)

    def __str__(self):
        ret = []
        if not self.top:
            ret += [self.lhs, '→']
        ret += self.rhs[:self.dot]
        ret.append('•')
        ret += self.rhs[self.dot:]
        return ' '.join(ret)
    def _repr_html_(self):
        return str(self)

def lr_automaton(g):
    """Construct the nondeterministic LR automaton for CFG g."""
    m = machines.FiniteAutomaton()
    m.set_start_state(DottedRule(None, [g.start_nonterminal], 0))

    s = g.start_nonterminal
    r = DottedRule(None, [s], 0)
    m.add_transition([[DottedRule(None, [s], 0)], [s]],
                     [[DottedRule(None, [s], 1)]])
    m.add_accept_state(DottedRule(None, [s], 1))
                     
    for [[lhs], rhs] in g.rules:
        if lhs == g.start_nonterminal:
            m.add_transition([[DottedRule(None, s, 0)], []],
                             [[DottedRule(lhs, rhs, 0)]])
        for i in range(len(rhs)):
            m.add_transition([[DottedRule(lhs, rhs, i)], [rhs[i]]],
                             [[DottedRule(lhs, rhs, i+1)]])
            if rhs[i] in g.nonterminals:
                for [[lhs1], rhs1] in g.rules:
                    if lhs1 == rhs[i]:
                        m.add_transition([[DottedRule(lhs, rhs, i)], []],
                                         [[DottedRule(lhs1, rhs1, 0)]])
        m.add_accept_state(DottedRule(lhs, rhs, len(rhs)))
                        
    return m

def from_cfg_lr0(g):
    """Convert a LR(0) grammar `g` to a DPDA. Does not assume that `g`
    generates an endmarked language."""
    
    lr = operations.determinize(lr_automaton(g))

    # Check for conflicts
    for q in lr.states:
        shift = False
        reduce = 0
        for dr in q:
            if dr.dot == len(dr.rhs):
                reduce += 1
            elif dr.rhs[dr.dot] not in g.nonterminals:
                shift = True
            if dr.top and dr.dot == 1:
                final = q
        if reduce > 1:
            raise ValueError(f"reduce/reduce conflict in state {q}")
        if shift and reduce > 0:
            raise ValueError(f"shift/reduce conflict in state {q}")

    # Build some indexes for faster access
    lr_bystate = {}
    for t in lr.get_transitions():
        [[q], [a]], [[r]] = t.lhs, t.rhs
        if len(r) == 0: continue # dead state
        lr_bystate[q, a] = r
    g_bylhs = collections.defaultdict(set)
    for [[lhs], rhs] in g.rules:
        g_bylhs[lhs].add(rhs)

    m = machines.PushdownAutomaton()

    m.set_start_state(lr.get_start_state())

    for (q, a), r in lr_bystate.items():
        if a in g.nonterminals:
            # Reduce
            for rhs in g_bylhs[a]:
                path = [q]
                s = q
                for x in rhs:
                    s = lr_bystate[s, x]
                    path.append(s)
                assert lr_bystate[path[0], a] == r
                m.add_transition(([path[-1]], [], reversed(path[:-1])), ([r], [path[0]]))
        else:
            # Shift
            m.add_transition(([q], [a], []), ([r], [q]))

    m.add_transition(([final], [], [lr.get_start_state()]), ("accept", []))
    m.add_accept_state("accept")
                                
    return m

def pda_to_cfg(m):
    """Convert a PDA to a CFG, using the construction of Sipser (3e) Lemma 2.27.

    Arguments:
      m (Machine): automaton to convert, which must be a PDA.

    Returns:
      Grammar: A CFG equivalent to `m`.
    """

    Tuple = syntax.Tuple
    
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
            raise NotImplementedError("transitions must either push or pop but not both or neither")

    # Add bottom symbol to stack
    start = fresh('start', m.states)
    bottom = fresh('$', stack_alphabet)
    stack_alphabet.add(bottom)
    push[bottom].append((start, [], [], m.get_start_state(), [bottom]))

    # Make automaton empty its stack before accepting
    accept = fresh('accept', m.states)
    empty = fresh('empty', m.states)
    for x in stack_alphabet:
        for q in m.get_accept_states():
            pop[x].append((q, [], [x], accept if x == bottom else empty, []))
        pop[x].append((empty, [], [x], accept if x == bottom else empty, []))

    g = Grammar()
    g.set_start_nonterminal(Tuple((start, accept)))

    # For each p, q, r, s \in Q, u \in \Gamma, and a, b \in \Sigma_\epsilon,
    # if \delta(p, a, \epsilon) contains (r, u) and \delta(s, b, u) contains
    # (q, \epsilon), put the rule A_{pq} -> a A_{rs} b in G.
    for u in stack_alphabet:
        for p, a, _, r, _ in push[u]:
            for s, b, _, q, _ in pop[u]:
                g.add_nonterminal(Tuple((p,q)))
                g.add_rule([Tuple((p,q))], list(a) + [Tuple((r,s))] + list(b))

    # For each p, q, r \in Q, put the rule A_{pq} -> A_{pr} A_{rq} in G.
    for p in m.states:
        for q in m.states:
            for r in m.states:
                g.add_nonterminal(Tuple((p,q)))
                g.add_rule([Tuple((p,q))], [Tuple((p,r)), Tuple((r,q))])

    # For each p \in Q, put the rule A_{pp} -> \epsilon in G
    for p in m.states:
        g.add_nonterminal(Tuple((p,p)))
        g.add_rule([Tuple((p,p))], [])

    return g

def to_grammar(m):
    if m.is_pushdown():
        return pda_to_cfg(m)
