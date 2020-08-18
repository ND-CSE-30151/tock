import collections
import dataclasses
import random
import itertools
from . import machines
from . import syntax
from . import operations
from . import runs
from . import trees

__all__ = ['Grammar', 'from_grammar', 'to_grammar', 'any_parse', 'only_parse', 'all_parses']

class Grammar:
    """A string-rewriting grammar."""
    def __init__(self):
        self.nonterminals = set()
        self.start_nonterminal = None
        self.rules = []

    @property
    def terminals(self):
        all = set()
        for lhs, rhs in self.rules:
            all.update(lhs)
            all.update(rhs)
        return all - self.nonterminals

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
        x = syntax.Symbol(x)
        self.add_nonterminal(x)
        self.start_nonterminal = x

    def add_nonterminal(self, x):
        """Add `x` to the nonterminal alphabet."""
        x = syntax.Symbol(x)
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
                return False
            if lhs[0] not in self.nonterminals:
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
                g.add_nonterminal(lhs)
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
          - ``"lr1"``: LR(1) deterministic bottom-up.

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
        elif mode == "lr0":
            return from_cfg_lr0(g)
        elif mode == "lr1":
            return from_cfg_lr1(g)
        else:
            raise ValueError("unknown mode '{}'".format(mode))
    else:
        raise NotImplementedError()

def from_cfg_topdown(g):
    terminals = g.terminals
    
    m = machines.PushdownAutomaton()
    m.set_start_state('start')
    m.add_transition(('start', [], []), ('loop', [g.start_nonterminal, '$']))
    for [[lhs], rhs] in g.rules:
        m.add_transition(('loop', [], lhs), ('loop', rhs))
    for a in terminals:
        m.add_transition(("loop", a, a), ("loop", []))
    m.add_transition(("loop", [], "$"), ("accept", []))
    m.add_accept_state("accept")
    
    return m

END = syntax.Symbol('-|')

def from_cfg_ll1(g):
    """Convert a CFG to a PDA. If the CFG is LL(1), the resulting PDA will
    be deterministic.
    """
    nullable = g.compute_nullable()
    first = g.compute_first(nullable)
    follow = g.compute_follow(nullable, first)
    terminals = g.terminals
    
    m = machines.PushdownAutomaton()
    m.set_start_state('start')
    m.add_transition(('start', [], []), ('loop', [g.start_nonterminal, '$']))
    for [[lhs], rhs] in g.rules:
        for c in terminals | {END}:
            if c in first[rhs] or (rhs in nullable and c in follow[lhs]):
                m.add_transition((c, [], lhs), (c, rhs))
    for a in terminals:
        m.add_transition(('loop', a, []), (a, []))
        m.add_transition((a, [], a), ('loop', []))
    m.add_transition(('loop', syntax.BLANK, []), (END, [])) # treat blank as endmarker
    m.add_transition((END, [], '$'), ('accept', []))
    m.add_accept_state("accept")
                                
    return m

def from_cfg_bottomup(g):
    terminals = g.terminals
    
    m = machines.PushdownAutomaton()
    m.set_start_state('start')
    m.add_transition(('start', [], []), ('loop', ['$']))
    for [[lhs], rhs] in g.rules:
        m.add_transition(("loop", [], reversed(rhs)), ("loop", lhs))
    for a in terminals:
        m.add_transition(("loop", a, []), ("loop", a))
    m.add_transition(("loop", [], [g.start_nonterminal, '$']), ("accept", []))
    m.add_accept_state("accept")
                                
    return m

@dataclasses.dataclass(frozen=True, order=True)
class DottedRule:
    top: bool
    lhs: syntax.Symbol
    rhs: tuple         # includes lookahead symbols
    dot: int           # position of dot
    end: int           # length of true rhs
    
    # change to DottedRule(lhs, rhs+lookahead, dotpos, lookpos)?
    # or: write lookahead like A b -> α b

    def __init__(self, lhs, rhs, dot, end=None):
        if lhs is None:
            object.__setattr__(self, 'top', True)
            object.__setattr__(self, 'lhs', None)
        else:
            object.__setattr__(self, 'top', False)
            object.__setattr__(self, 'lhs', lhs)
        object.__setattr__(self, 'rhs', tuple(rhs))
        object.__setattr__(self, 'dot', dot)
        if end is None:
            object.__setattr__(self, 'end', len(rhs))
        else:
            object.__setattr__(self, 'end', end)

    def move(self, dot):
        return DottedRule(self.lhs, self.rhs, dot, self.end)

    def __str__(self):
        toks = list(self.rhs)
        if self.end < len(self.rhs):
            toks[self.end] = '(' + toks[self.end]
            toks[-1] = toks[-1] + ')'
        toks[self.dot:self.dot] = ['.']
        if not self.top:
            toks[0:0] = [self.lhs, '→']
        return ' '.join(map(str, toks))
    def _repr_html_(self):
        return str(self)

def intersect_stack(p, m):
    """Given a PDA `p` and DFA `m`, construct a new PDA whose stack
    language is the intersection of the stack language of `p`
    (bottom-to-top) and the language of `m`.

    This construction is the same as Hopcroft and Ullman (1e), page 254.
   
    `p` can push and pop multiple symbols, and the resulting PDA does
    push and pop multiple symbols.
    """
    if not p.is_pushdown():
        raise ValueError('m must be a pushdown automaton')
    if not m.is_finite():
        raise ValueError('m must be a finite automaton')
    if not m.is_deterministic():
        raise NotImplementedError('m must be deterministic')
    
    m_bystate = {}
    for t in m.get_transitions():
        [[q], [a]], [[r]] = t.lhs, t.rhs
        m_bystate[q, a] = r
    mf = m.get_accept_states()
    
    pm = machines.PushdownAutomaton()

    # pm has the same states as p, plus a new start state.
    # pm's stack contains paths of m, alternating between states of m
    # and input symbols of m (= stack symbols of p).
    # For LR parsing, it's not necessary to store the latter (e.g.,
    # Sipser (3e) Lemma 2.58), but in general
    # m might have more than one transition between a pair of states.
    
    pq1 = p.get_start_state()
    pq0 = fresh(pq1, p.states)
    pm.set_start_state(pq0)
    pm.add_transition([[pq0], [], []], [[pq1], [m.get_start_state()]])

    for pt in p.get_transitions():
        [[pq], pa, px], [[pr], py] = pt.lhs, pt.rhs
        for mq in m.states:
            pmx = [mq]
            for x in reversed(px):
                pmx += [x, m_bystate[pmx[-1], x]]
            pmy = [mq]
            for y in reversed(py):
                pmy += [y, m_bystate[pmy[-1], y]]

            if pmx[-1] in mf and pmy[-1] in mf:
                pm.add_transition([[pq], pa, reversed(pmx)], [[pr], reversed(pmy)])
                    
    pm.add_accept_states(p.get_accept_states())
    return pm

def renumber_states(m, verbose=False):
    if not m.is_finite():
        raise ValueError()
    index = {}
    for i, q in enumerate(sorted(m.states)):
        index[q] = i
        if verbose:
            print(f"{i}\t{q}")
    mr = machines.FiniteAutomaton()
    mr.set_start_state(index[m.get_start_state()])
    mr.add_accept_states([index[q] for q in m.get_accept_states()])
    for t in m.get_transitions():
        [[q], [a]], [[r]] = t.lhs, t.rhs
        mr.add_transition([[index[q]], [a]], [[index[r]]])
    return mr

def lr_automaton(g, k=0):
    """Construct the nondeterministic LR(k) automaton for CFG g."""

    if k == 1:
        nullable = g.compute_nullable()
        first = g.compute_first(nullable)
        follow = g.compute_follow(nullable, first)
    elif k > 1:
        raise NotImplementedError()
    
    g_bylhs = collections.defaultdict(list)
    for [[lhs], rhs] in g.rules:
        g_bylhs[lhs].append(rhs)
        
    # Add top pseudo-rule
    g_bylhs[None] = [syntax.String([g.start_nonterminal])]
    if k == 1: follow[None] = [END]

    m = machines.FiniteAutomaton()
    m.set_start_state('start')
    
    # Nonstandardly read a $ because from_cfg_bottomup pushes a $ at
    # the bottom of its stack.
    m.add_transition(['start', '$'],
                     [[DottedRule(None, [g.start_nonterminal] + [END]*k, 0, 1)]])
    
    for lhs in g_bylhs:
        for rhs in g_bylhs[lhs]:
            if k == 0:
                looks = [[]]
            elif k == 1:
                looks = [[x] for x in follow[lhs]]
            for look in looks:
                dr = DottedRule(lhs, list(rhs)+look, 0, len(rhs))
                for i, x in enumerate(dr.rhs):
                    # Shift
                    m.add_transition([[dr.move(i)], [x]], [[dr.move(i+1)]])
                    # Predict
                    if x not in g.nonterminals:
                        continue
                    if k == 0:
                        looks1 = [[]]
                    elif k == 1:
                        looks1 = [[x] for x in first[rhs[i:]]]
                        if rhs[i:] in nullable:
                            looks1 += looks
                    for rhs1 in g_bylhs[x]:
                        for look1 in looks1:
                            m.add_transition([[dr.move(i)], []],
                                             [[DottedRule(x, list(rhs1)+look1, 0, len(rhs1))]])
                m.add_accept_state(dr.move(len(dr.rhs)))
                
    return m

def from_cfg_lr0(g):
    """Convert a CFG to a PDA. If the CFG is LR(0), the resulting PDA
    will be deterministic.
    """

    p = from_cfg_bottomup(g)
    lr = lr_automaton(g, 0)
    lr = operations.determinize(lr)
    lr = operations.prefix(lr)
    lr = renumber_states(lr)
    
    return intersect_stack(p, lr)

def from_cfg_lr1(g):
    """Convert a CFG to a PDA. If the CFG is LR(1), the resulting PDA
    will be deterministic.
    """
    terminals = g.terminals
    
    m = machines.PushdownAutomaton()
    m.set_start_state('start')
    m.add_transition(('start', [], []), ('loop', '$'))
    # reduce
    for [[lhs], rhs] in g.rules:
        for a in terminals | {END}:
            m.add_transition(('loop', [], [a] + list(reversed(rhs))), ('loop', [a, lhs]))
    # shift
    for a in terminals:
        m.add_transition(('loop', a, []), ('loop', a))
    m.add_transition(('loop', syntax.BLANK, []), ('loop', END))
    # accept
    m.add_transition(('loop', [], [END, g.start_nonterminal, '$']), ('accept', []))
    m.add_accept_state('accept')
                                
    lr = lr_automaton(g, 1)
    lr = operations.determinize(lr)
    lr = operations.prefix(lr)
    lr = renumber_states(lr)
    
    return intersect_stack(m, lr)
    
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

def pda_paths(r):
    # To do: move to runs.py
    # Index the edges of r in reverse
    ants = collections.defaultdict(list)
    for u in r.edges:
        for v in r.edges[u]:
            for e in r.edges[u][v]:
                ants[v].append((e, u))

    def visit(v):
        axiom = False
        if 'start' in r.nodes[v]:
            axiom = True
        else:
            assert len(ants[v]) > 0
            for e, u in ants[v]:
                if 'prev' in e:
                    for p1 in visit(e['prev']):
                        for p2 in visit(u):
                            yield p1 + p2
                elif 'transition' in e:
                    for p in visit(u):
                        yield p + [e['transition']]
                else:
                    axiom = True
        if axiom:
            yield []

    for v in r.nodes:
        if 'accept' in r.nodes[v]:
            yield from visit(v)

def pda_path_to_tree(path, mode='bottomup'):
    if mode != 'bottomup':
        raise NotImplementedError
    stack = []
    for trans in path:
        [q], a, x = trans.lhs
        [r], _, y = trans.rhs
        if q == r == 'loop':
            if len(a) == 1:
                stack.append(trees.Tree(a[0]))
            elif len(x) == 0:
                stack.append(trees.Tree(y[0], [trees.Tree('ε')]))
            else:
                stack[-len(x):] = [trees.Tree(y[0], stack[-len(x):])]
    assert len(stack) == 1
    return stack[0]

def only_parse(g, w):
    m = from_grammar(g, mode='bottomup')
    r = runs.run_pda(m, w, show_stack=0, keep_nodes=True)
    paths = list(itertools.islice(pda_paths(r), 2))
    if len(paths) == 0:
        raise ValueError('no parse')
    elif len(paths) == 1:
        return pda_path_to_tree(paths[0])
    else:
        raise ValueError('more than one possible parse')
                
def any_parse(g, w):
    m = from_grammar(g, mode='bottomup')
    r = runs.run_pda(m, w, show_stack=0, keep_nodes=True)
    paths = pda_paths(r)
    try:
        path = next(paths)
    except StopIteration:
        raise ValueError('no parse')
    return pda_path_to_tree(path)

def all_parses(g, w):
    m = from_grammar(g, mode='bottomup')
    r = runs.run_pda(m, w, show_stack=0, keep_nodes=True)
    paths = pda_paths(r)
    for path in paths:
        yield pda_path_to_tree(path)
