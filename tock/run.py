import collections
from . import machines
from . import graphs

__all__ = ['run', 'run_bfs', 'run_pda']

def run(m, w, trace=False, steps=1000, show_stack=3):
    """Runs an automaton, automatically selecting a search method."""

    # Check to see whether run_pda can handle it.
    is_pda = True
    stack = None
    if not m.oneway:
        is_pda = False
    for s in range(m.num_stores):
        if s == m.input:
            pass
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
        return run_pda(m, w, stack=stack, trace=trace, show_stack=show_stack)
    else:
        if trace: print("using breadth-first search")
        return run_bfs(m, w, trace=trace, steps=steps)

def run_bfs(m, w, trace=False, steps=1000):
    """Runs an automaton using breadth-first search."""
    from .machines import Store, Configuration, Transition

    agenda = collections.deque()
    chart = {}

    # Initial configuration
    config = list(m.start_config)
    w = Store(w)
    config[m.input] = w
    config = Configuration(config)

    chart[config] = 0
    agenda.append(config)
    run = graphs.Graph()
    run.attrs['rankdir'] = 'LR'
    run.add_node(config, {'start': True})

    while len(agenda) > 0:
        tconfig = agenda.popleft()

        if trace: print("trigger: {}".format(tconfig))

        for aconfig in m.accept_configs:
            if aconfig.match(tconfig):
                run.add_node(tconfig, {'accept': True})

        if chart[tconfig] == steps:
            if trace: print("maximum number of steps reached")
            run.add_node(tconfig, {'incomplete': True})
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

    # If input tape is one-way, then rank all nodes by input position
    if m.oneway:
        for q in run.nodes:
            ql = list(q)
            run.nodes[q]['rank'] = ql.pop(m.input)
            run.nodes[q]['label'] = Configuration(ql)
        for i in range(len(w)+1):
            r = 'rank{}'.format(i)
            run.add_node(r, {'rank' : Store(w[i:]), 'style' : 'invisible'})
            if i > 0:
                run.add_edge(rprev, r, {'color': 'white', 'label' : w[i-1]})
            rprev = r

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

    from .machines import Store, Configuration, Transition

    agenda = collections.deque()
    chart = set()
    index_left = collections.defaultdict(set)
    index_right = collections.defaultdict(set)
    backpointers = collections.defaultdict(set)
    run = graphs.Graph()
    run.attrs['rankdir'] = 'LR'

    # which position the state, input and stack are in
    if not m.has_stack(stack):
        raise ValueError("store %s must be a stack" % stack)

    # how much of the stack is not elided
    show_stack = max(show_stack, 
                     max(len(t.lhs[stack]) for t in m.transitions), 
                     max(len(c[stack]) for c in m.accept_configs))

    # Axiom
    config = list(m.start_config)
    w = Store(w)
    config[m.input] = w
    config = Configuration(config)

    # draw input symbols
    for i in range(len(w)+1):
        r = 'rank{}'.format(i)
        run.add_node(r, {'rank' : Store(w[i:]), 'style' : 'invisible'})
        if i > 0:
            run.add_edge(rprev, r, {'color': 'white', 'label' : w[i-1]})
        rprev = r

    def get_node(parent, child):
        if parent is not None:
            # In the run graph, we don't show the parent,
            # but if there is one, add a ...
            child = list(child)
            child[stack] = Store(child[stack].values + ["..."], child[stack].position)
        return Configuration(child)

    def add_node(parent, child, attrs=None):
        node = get_node(parent, child)
        attrs = {} if attrs is None else dict(attrs)
        label = list(node)
        attrs['rank'] = label.pop(m.input)
        attrs['label'] = Configuration(label)
        run.add_node(node, attrs)

    agenda.append((None, config))
    add_node(None, config, {'start': True})

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

        for aconfig in m.accept_configs:
            if aconfig.match(child) and (parent is None or len(child[stack]) == show_stack):
                add_node(parent, child, {'accept': True})

        # The stack shows too many items (push)
        if len(child[stack]) > show_stack:
            grandchild = child.deepcopy()
            del grandchild[stack].values[-1]
            add(child, grandchild)
            index_right[child].add(parent)
            for ant in backpointers[get_node(parent, child)]:
                backpointers[get_node(child, grandchild)].add(ant)

            # This item can also be the left antecedent of the Pop rule
            for grandchild in index_left[child]:
                grandchild = grandchild.deepcopy()
                grandchild[stack].values.append(child[stack][-1])
                add(parent, grandchild)
                for ant in backpointers[get_node(parent, child)]:
                    backpointers[get_node(parent, grandchild)].add(ant)

        # The stack shows too few items (pop)
        elif parent is not None and len(child[stack]) < show_stack:
            aunt = child.deepcopy()
            if len(parent[stack]) == 0:
                assert False
            else:
                aunt[stack].values.append(parent[stack][-1])
            index_left[parent].add(child)

            for grandparent in index_right[parent]:
                add(grandparent, aunt)

            for ant in backpointers[get_node(parent, child)]:
                backpointers[get_node(grandparent, aunt)].add(ant)

        # The stack is just right
        else:
            add_node(parent, child)
            for transition in m.transitions:
                if transition.match(child):
                    sister = transition.apply(child)
                    add(parent, sister)
                    backpointers[get_node(parent, sister)].add(get_node(parent, child))

    # Add run edges only between configurations whose stack is
    # just right
    for config2 in run.nodes:
        for config1 in backpointers[config2]:
            run.add_edge(config1, config2)

    return run
