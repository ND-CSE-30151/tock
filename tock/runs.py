"""This module contains functions for simulating machines on
strings. Normally, `run` is the only function one needs to use."""

import collections
from . import machines
from . import graphs

__all__ = ['run', 'run_bfs', 'run_pda']

def run(m, w, trace=False, steps=1000, show_stack=3):
    """Runs machine `m` on string `w`, automatically selecting a search method.

    Arguments:
    
        m (Machine):      The machine to run.
        w (String):       The string to run on.
        trace (bool):     Print the steps of the simulation to stdout.
        steps (int):      Maximum number of steps to run the simulation.
        show_stack (int): For PDAs, the maximum depth of the stack to show.
    
    Returns:
    
        A Graph whose nodes are the configurations reachable from the
        start configuration (which has the attribute `start=True`). It has
        an accept configuration (attribute `accept=True`) iff `m` accepts
        `w`.
    """

    # Check to see whether run_pda can handle it.
    is_pda = True

    stack = None
    if m.store_types[m.input] != machines.STREAM:
        is_pda = False
    for s in range(m.num_stores):
        if s == m.input:
            if not m.has_input_stream(s):
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
        return run_pda(m, w, stack=stack, trace=trace, show_stack=show_stack)
    else:
        if trace: print("using breadth-first search")
        return run_bfs(m, w, trace=trace, steps=steps)

def run_bfs(m, w, trace=False, steps=1000):
    """Runs machine `m` on string `w` using breadth-first search.

    Arguments:

        m (Machine):  The machine to run.
        w (String):   The string to run on.
        trace (bool): Print the steps of the simulation to stdout.
        steps (int):  Maximum number of steps to run the simulation.

    Returns:

        Same as `run`.
    """
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
                run.add_edge(tconfig, nconfig, {'transition': rule})

    # If input tape is one-way, then rank all nodes by input position
    if m.store_types[m.input] == machines.STREAM:
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

def run_pda(m, w, stack=2, trace=False, show_stack=3, keep_nodes=False):
    """Runs a nondeterministic pushdown automaton using a cubic-time
    algorithm based on: Bernard Lang, "Deterministic techniques for
    efficient non-deterministic parsers." doi:10.1007/3-540-06841-4_65

    Arguments:

        m (Machine):       The machine to run, which must be a PDA.
        w (String):        The string to run on.
        stack (int):       Which store is the stack.
        trace (bool):      Print the steps of the simulation to stdout.
        show_stack (int):  The maximum depth of the stack to show.
        keep_nodes (bool): Keep all nodes that aren't PDA configurations

    Returns:

        Same as `run`. Because stacks are truncated, the number of nodes
        in the returned graph may be less than the actual number of
        configurations (which may be infinite).

    """

    """The items one have of the following two forms:

       - [None => r, j, Y], in which case Y is a complete stack and
         (r, j, Y) is reachable from the start configuration.

       - [q, i, Xz => r, j, Y], in which case for any R, (q, i, XzR)
         can reach (r, j, YzR).

    The inference rules are:

    Axiom:
    
    ------------------
    [None => q0, 0, &]
    
    Push:
    
    [q, i, Yz => r, j, Xy']
    -----------------------
    [r, j, Xy' => r, j, X]
    
    Pop:
    
    [q, i, Yz => r, j, Xy'] [r, j, Xy' => s, k, Z]
    ----------------------------------------------
                 [q, i, Yz => s, k, Zy']

    Apply:

     [q, i, Xz => r, j, Y]
    ------------------------ (r, j, Y) yields (r', j', Y')
    [q, i, Xz => r', j', Y']

    """

    from .machines import Store, Configuration, Transition

    agenda = collections.deque()
    chart = set()
    index_left = collections.defaultdict(set)
    index_right = collections.defaultdict(set)
    run = graphs.Graph()
    run.attrs['rankdir'] = 'LR'

    if not m.has_stack(stack):
        raise ValueError(f'store {stack} must be a stack')

    # how much of the stack is not elided
    show_stack = max(show_stack, 
                     max(len(t.lhs[stack]) for t in m.transitions), 
                     max(len(c[stack]) for c in m.accept_configs))

    def pop(config):
        stores = []
        for si in range(len(config)):
            if si == stack:
                stores.append(Store(config[si][:-1], config[si].position))
            else:
                stores.append(config[si])
        return Configuration(stores)
    
    def push(config, x):
        stores = []
        for si in range(len(config)):
            if si == stack:
                stores.append(Store(config[si].values+(x,), config[si].position))
            else:
                stores.append(config[si])
        return Configuration(stores)

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
        """Convert a parent-child pair into a single Configuration,
        because the nodes of the run Graph must be Configurations."""
        if parent is not None:
            child = list(child)
            child[stack] = Store(child[stack].values + (f'…{hash(parent)}',), child[stack].position)
        return Configuration(child)

    def add_node(parent, child, attrs=None):
        node = get_node(parent, child)
        attrs = {} if attrs is None else dict(attrs)
        label = list(node)
        if len(label[stack])> 0 and label[stack][-1].startswith('…'):
            label[stack] = Store(label[stack][:-1].values + ('…',), label[stack].position)
        attrs['rank'] = label.pop(m.input)
        attrs['label'] = Configuration(label)
        run.add_node(node, attrs)

    agenda.append((None, config))
    add_node(None, config, {'start': True})

    def add(parent, child, aparent, achild, oparent=None, ochild=None, transition=None):
        if (parent, child) in chart:
            if trace: print("merge: {} => {}".format(parent, child))
        else:
            chart.add((parent, child))
            if trace: print("add: {} => {}".format(parent, child))
            agenda.append((parent, child))
        attrs = {}
        if ochild:
            attrs['prev'] = get_node(oparent, ochild)
        if transition:
            attrs['transition'] = transition
        run.add_edge(get_node(aparent, achild),
                     get_node(parent, child),
                     attrs)

    while len(agenda) > 0:
        parent, child = agenda.popleft()
        if trace: print("trigger: {} => {}".format(parent, child))
        
        add_node(parent, child)

        for aconfig in m.accept_configs:
            if (aconfig.match(child) and
                (parent is None or len(child[stack]) == show_stack)):
                add_node(parent, child, {'accept': True})

        if len(child[stack]) > show_stack:
            # The stack shows too many items (Push)
            grandchild = pop(child)
            add(child, grandchild, parent, child)
                         
            # Left antecedent of the Pop rule
            index_right[child].add(parent)
            for grandchild in index_left[child]:
                grandchild1 = push(grandchild, child[stack][-1])
                add(parent, grandchild1, child, grandchild, parent, child)

        # The stack shows too few items (right antecedent of Pop rule)
        elif parent is not None and len(child[stack]) < show_stack:
            index_left[parent].add(child)
            aunt = push(child, parent[stack][-1])
            for grandparent in index_right[parent]:
                add(grandparent, aunt, parent, child, grandparent, parent)

        # The stack is just right (Apply)
        else:
            for transition in m.transitions:
                if transition.match(child):
                    sister = transition.apply(child)
                    add(parent, sister, parent, child, transition=transition)

    # Remove any edges that don't have transitions
    if not keep_nodes:
        done = False
        deleted_nodes = set()
        while not done:
            done = True
            for u in run.edges:
                new_edges = {}
                for v in run.edges[u]:
                    for e in run.edges[u][v]:
                        if 'transition' not in e and 'label' not in e:
                            assert u != v
                            for w in run.edges.get(v, []):
                                new_edges.setdefault(w, []).extend(run.edges[v][w])
                            deleted_nodes.add(v)
                            done = False
                        else:
                            new_edges.setdefault(v, []).append(e)
                run.edges[u] = new_edges
        for v in deleted_nodes:
            del run.nodes[v]
            if v in run.edges: del run.edges[v]

    return run
