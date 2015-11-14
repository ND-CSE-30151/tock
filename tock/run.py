import collections
from . import machines
from . import syntax

__all__ = ['run', 'run_bfs', 'run_pda']

def run(m, w, trace=False, steps=1000, show_stack=3):
    """Runs an automaton, automatically selecting a search method."""

    # Check to see whether run_pda can handle it.
    is_pda = True
    stack = None
    for s in range(m.num_stores):
        if s == m.input:
            if not m.has_input(s):
                is_pda = False
        elif m.has_cell(s): # anything with finite number of configs would do
            pass
        elif m.has_stack(s):
            if stack is None:
                stack = s
            else:
                is_pda = False
        else:
            is_pda = False

    if is_pda and stack is not None:
        if trace: print("using modified Lang algorithm")
        return run_pda(m, w, trace=trace, show_stack=show_stack)
    else:
        if trace: print("using breadth-first search")
        return run_bfs(m, w, trace=trace, steps=steps)

def run_bfs(m, w, trace=False, steps=1000):
    """Runs an automaton using breadth-first search."""
    from .machines import Store, Transition

    agenda = collections.deque()
    chart = {}

    # Initial configuration
    input_tokens = syntax.lexer(w)
    config = list(m.start_config)
    config[m.input] = Store(input_tokens)
    config = tuple(config)

    chart[config] = 0
    agenda.append(config)
    run = Run(m)
    run.set_start_config(config)

    # Final configurations
    # Since there is no Configuration class, we need to make a fake Transition
    final_transitions = []
    for config in m.accept_configs:
        final_transitions.append(Transition(config, [[]]*m.num_stores))

    while len(agenda) > 0:
        tconfig = agenda.popleft()

        if trace: print("trigger: {}".format(tconfig))

        for t in final_transitions:
            if t.match(tconfig):
                run.add_accept_config(tconfig)

        if chart[tconfig] == steps:
            if trace: print("maximum number of steps reached")
            run.add_ellipsis(tconfig, None)
            continue

        for rule in m.transitions:
            if trace: print("rule: {}".format(rule))
            if rule.match(tconfig):
                nconfig = rule.apply(tconfig)

                if nconfig in chart:
                    assert chart[nconfig] <= chart[tconfig]+1
                    if trace: print("merge: {}".format(nconfig))
                else:
                    chart[nconfig] = chart[tconfig]+1
                    if trace: print("add: {}".format(nconfig))
                agenda.append(nconfig)
                run.add_edge(tconfig, nconfig)

    return run

def run_pda(m, w, stack=2, trace=False, show_stack=3):
    """Runs a nondeterministic pushdown automaton using the cubic
    algorithm of: Bernard Lang, "Deterministic techniques for efficient 
    non-deterministic parsers." doi:10.1007/3-540-06841-4_65 .

    `m`: the pushdown automaton
    `w`: the input string

    Store 1 is assumed to be the input, and store 2 is assumed to be the stack.
    Currently we don't allow any other stores, though additional cells would
    be fine.
    """

    """The items are pairs of configurations (parent, child), where

       - parent is None and child's stack has no elided items
       - child has one more elided item than parent

    The inference rules are:

    Axiom:
    
    ------------------
    [None => q0, 0, &]
    
    Push:
    
    [q, i, yz => r, j, xy']
    -----------------------
    [r, j, xy' => r, j, x]
    
    Pop:
    
    [q, i, yz => r, j, xy'] [r, j, xy' => s, k, &]
    ----------------------------------------------
                 [q, i, yz => s, k, y']

    Apply: applies a transition to child

    """

    from .machines import Store, Transition

    agenda = collections.deque()
    goals = []
    chart = set()
    index_left = collections.defaultdict(set)
    index_right = collections.defaultdict(set)
    backpointers = collections.defaultdict(set)
    visible = set()
    run = Run(m)

    # which position the state, input and stack are in
    if not m.has_stack(stack):
        raise ValueError("store %s must be a stack" % stack)

    # how much of the stack is not elided
    show_stack = max(show_stack, 
                     max(len(t.lhs[stack]) for t in m.transitions), 
                     max(len(c[stack]) for c in m.accept_configs))

    # Axiom
    input_tokens = syntax.lexer(w)
    config = list(m.start_config)
    config[m.input] = Store(input_tokens)
    config = tuple(config)

    def simplify(parent, child):
        """Map a parent=>child item into a node in the run graph.
           If parent is not None, just append a ..."""
        if parent is None:
            return child
        else:
            child = list(child)
            child[stack] = Store(child[stack].values + ["..."], child[stack].position)
            return tuple(child)

    agenda.append((None, config))
    run.set_start_config(simplify(None, config))

    # Final configurations
    # Since there is no Configuration class, we need to make a fake Transition
    final_transitions = []
    for config in m.accept_configs:
        final_transitions.append(Transition(config, [[]]*m.num_stores))

    def add(parent, child):
        if (parent, child) in chart:
            if trace: print("merge: {} => {}".format(parent, child))
        else:
            chart.add((parent, child))
            if trace: print("add: {} => {}".format(parent, child))
            agenda.append((parent, child))

    while len(agenda) > 0:
        parent, child = agenda.popleft()
        if trace: print("trigger: {} => {}".format(parent, child))

        for t in final_transitions:
            if t.match(child):
                run.add_accept_config(simplify(parent, child))

        # The stack shows too many items (push)
        if len(child[stack]) > show_stack:
            grandchild = tuple(s.copy() for s in child)
            del grandchild[stack].values[-1]
            add(child, grandchild)
            index_right[child].add(parent)
            for ant in backpointers[simplify(parent, child)]:
                backpointers[simplify(child, grandchild)].add(ant)

            # This item can also be the left antecedent of the Pop rule
            for grandchild in index_left[child]:
                grandchild = tuple(s.copy() for s in grandchild)
                grandchild[stack].values.append(child[stack][-1])
                add(parent, grandchild)
                for ant in backpointers[simplify(parent, child)]:
                    backpointers[simplify(parent, grandchild)].add(ant)

        # The stack shows too few items (pop)
        elif parent is not None and len(child[stack]) < show_stack:
            aunt = tuple(s.copy() for s in child)
            if len(parent[stack]) == 0:
                assert False
            else:
                aunt[stack].values.append(parent[stack][-1])
            index_left[parent].add(child)

            for grandparent in index_right[parent]:
                add(grandparent, aunt)

            for ant in backpointers[simplify(parent, child)]:
                backpointers[simplify(grandparent, aunt)].add(ant)

        # The stack is just right
        else:
            run.configs.add(simplify(parent, child))
            for transition in m.transitions:
                if transition.match(child):
                    sister = transition.apply(child)
                    add(parent, sister)
                    backpointers[simplify(parent, sister)].add(simplify(parent, child))

    # Add run edges only between configurations whose stack is
    # just right
    for config2 in run.configs:
        for config1 in backpointers[config2]:
            run.add_edge(config1, config2)

    return run

def ascii_to_html(s):
    s = str(s)
    s = s.replace("&", "&epsilon;")
    s = s.replace("->", "&rarr;")
    s = s.replace(">", "&gt;")
    s = s.replace("...", "&hellip;")
    return s

class Run(object):
    def __init__(self, machine):
        self.machine = machine
        self.configs = set()
        self.edges = set()
        self.ellipses = set()
        self.start_config = None
        self.accept_configs = set()

    def add_edge(self, from_config, to_config):
        self.configs.add(from_config)
        self.configs.add(to_config)
        self.edges.add((from_config, to_config))

    def add_ellipsis(self, from_config, to_config):
        if from_config is not None:
            self.configs.add(from_config)
        if to_config is not None:
            self.configs.add(to_config)
        self.ellipses.add((from_config, to_config))

    def set_start_config(self, config):
        self.start_config = config
        self.configs.add(config)

    def add_accept_config(self, config):
        self.accept_configs.add(config)
        self.configs.add(config)

    def _ipython_display_(self):
        def label(config): 
            # Label nodes by config
            return ascii_to_html(','.join(map(str, (config[0][0],) + config[1:])))
        def label_no_input(config): 
            # Label nodes by config sans input (second store)
            return ascii_to_html(','.join(map(str, (config[0][0],) + config[2:])))
        def rank(config): 
            # Rank nodes by input position
            l = len([x for x in config[self.machine.input] if x != syntax.BLANK])
            return (-l, config[1])

        result = []
        result.append("digraph {")
        result.append("  rankdir=TB;")
        result.append('  node [fontname=Courier,fontsize=10,shape=box,style=rounded,height=0,width=0,margin="0.055,0.042"];')
        result.append("  edge [arrowhead=vee,arrowsize=0.5];")

        result.append('  START[shape=none,label=""];\n')

        one_way_input = self.machine.has_input(self.machine.input)

        # assign an id to each config
        config_id = {}
        for config in self.configs:
            if config not in config_id:
                config_id[config] = len(config_id)

        for config in self.configs:
            attrs = {}
            if one_way_input:
                attrs['label'] = '<{}>'.format(label_no_input(config))
            else:
                attrs['label'] = '<{}>'.format(label(config))

            if config in self.accept_configs:
                attrs['peripheries'] = 2

            result.append('  %s[%s];' % (config_id[config], ','.join('{}={}'.format(key,val) for key,val in attrs.items())))
            if config == self.start_config:
                result.append('  START -> %s;' % (config_id[config]))

        if one_way_input:
            # If a node has a predecessor in a previous rank
            # as well as in the same rank, let the former determine
            # the position of the node

            nonepsilon = set()
            for from_config, to_config in self.edges:
                if rank(to_config) > rank(from_config):
                    nonepsilon.add(to_config)
            for from_config, to_config in self.edges:
                if rank(to_config) == rank(from_config) and to_config in nonepsilon:
                    result.append("  %s -> %s[constraint=false];" % (config_id[from_config], config_id[to_config]))
                else:
                    result.append("  %s -> %s;" % (config_id[from_config], config_id[to_config]))

        else:
            for from_config, to_config in self.edges:
                result.append("  %s -> %s;" % (config_id[from_config], config_id[to_config]))

        for from_config, to_config in self.ellipses:
            if to_config is None:
                cid = config_id[from_config]
                result.append('  DOTS_%s[shape=none,label=""];\n' % (cid,))
                result.append("  %s -> DOTS_%s[dir=none,style=dotted];" % (cid, cid))
            elif from_config is None:
                cid = config_id[to_config]
                result.append('  DOTS_%s[shape=none,label=""];\n' % (cid,))
                result.append("  DOTS_%s -> %s[dir=none,style=dotted];" % (cid, cid))

        if one_way_input:
            ranks = collections.defaultdict(list)
            for config in self.configs:
                ranks[rank(config)].append(str(config_id[config]))
            prev_ri = None
            for ri, ((level, rank), nodes) in enumerate(sorted(ranks.items())):
                result.append('  rank%s[shape=plaintext,label=<%s>];' % (ri, ascii_to_html(str(rank))))
                result.append("{ rank=same; rank%s %s }" % (ri, " ".join(nodes)))
                if prev_ri is not None:
                    result.append('  rank%s -> rank%s[style=invis];' % (prev_ri, ri))
                prev_ri = ri

        result.append("}")

        from IPython.display import display
        from .viz import viz
        display(viz("\n".join(result)))
