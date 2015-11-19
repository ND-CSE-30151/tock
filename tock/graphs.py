from . import machines

__all__ = ['to_graph', 'write_dot', 'read_tgf']

class Graph(object):
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.attrs = {}

    def add_node(self, v, attrs):
        if v in self.nodes:
            self.nodes[v].update(attrs)
        self.nodes[v] = attrs

    def add_edge(self, u, v, attrs):
        if u not in self.nodes: self.nodes[u] = {}
        if v not in self.nodes: self.nodes[v] = {}
        self.edges.setdefault(u, {})
        self.edges[u].setdefault(v, [])
        self.edges[u][v].append(attrs)

    def __getitem__(self, u):
        return self.edges[u]

    def _repr_dot_(self):
        result = []
        result.append('digraph {')
        for key, val in self.attrs.items():
            result.append('  {}={};'.format(key, val))
        result.append('  node [fontname=Courier,fontsize=10,shape=box,style=rounded,height=0,width=0,margin="0.055,0.042"];')
        result.append('  edge [arrowhead=vee,arrowsize=0.5,fontname=Courier,fontsize=9];')

        result.append('  START[shape=none,label=""];\n')

        index = {}

        # only show nodes that have edges
        nodes = set()
        for u in self.edges:
            nodes.add(u)
            for v in self.edges[u]:
                nodes.add(v)

        for i, q in enumerate(sorted(nodes)):
            index[q] = i
            if self.nodes[q].get('accept', False):
                result.append('  {}[label="{}",peripheries=2];'.format(i, q))
            else:
                result.append('  {}[label="{}"];'.format(i, q))
            if self.nodes[q].get('start', False):
                result.append('  START -> {}'.format(i))

        for u in self.edges:
            for v in self.edges[u]:
                labels = []
                for e in self.edges[u][v]:
                    labels.append('<tr><td>{}</td></tr>'.format(e['label']._repr_html_()))
                label = '<table border="0" cellpadding="1">{}</table>'.format(''.join(labels))
                result.append('  {} -> {}[label=<{}>];'.format(index[u], index[v], label))

        result.append('}')
        return '\n'.join(result)

    graphviz_impl = None

    def _ipython_display_(self):
        from IPython.display import display
        from .viz import viz
        display(viz(self._repr_dot_()))

def read_tgf(filename):
    """Reads a file in Trivial Graph Format."""
    g = Graph()
    with open(filename) as file:
        states = {}

        # Nodes
        for line in file:
            line = line.strip()
            if line == "": 
                continue
            elif line == "#":
                break
            i, q = line.split(None, 1)
            q, attrs = syntax.string_to_state(q)
            states[i] = q
            g.add_node(q, attrs)

        # Edges
        for line in file:
            line = line.strip()
            if line == "": 
                continue
            i, j, t = line.split(None, 2)
            q, r = states[i], states[j]
            t = syntax.string_to_transition(t)
            g.add_edge(q, r, {'label':t})

    return from_graph(g)

def single_value(s):
    s = set(s)
    if len(s) != 1:
        raise ValueError()
    return s.pop()

def from_graph(g):
    transitions = []

    for q in g.edges:
        for r in g.edges[q]:
            for e in g.edges[q][r]:
                t = e['label']
                transitions.append((([q],)+t.lhs, ([r],)+t.rhs))

    num_stores = single_value(len(lhs) for lhs, rhs in transitions)
    m = machines.Machine(num_stores, state=0, input=1)
    m.add_accept_config(["ACCEPT"] + [[]]*(num_stores-1))

    for q in g.nodes:
        if g.nodes[q].get('start', False):
            if m.start_config is not None:
                raise ValueError("more than one start state")
            m.set_start_state(q)
        if g.nodes[q].get('accept', False):
            m.add_accept_state(q)

    for lhs, rhs in transitions:
        m.add_transition(lhs, rhs)

    return m

def write_dot(x, filename):
    if isinstance(x, machines.Machine):
        x = to_graph(x)
    if not isinstance(x, Graph):
        raise TypeError("Only Machines and Graphs can be written as DOT files")
    with open(filename, "w") as file:
        file.write(x._repr_dot_())

def to_graph(m):
    g = Graph()
    g.attrs['rankdir'] = 'LR'
    if m.state is None: raise ValueError("no state defined")
    [q] = m.start_config[m.state]
    g.add_node(q, {'start': True})
    for config in m.accept_configs:
        [q] = config[m.state]
        g.add_node(q, {'accept': True})
    for t in m.get_transitions():
        lhs = list(t.lhs)
        rhs = list(t.rhs)
        [q] = lhs.pop(m.state)
        [r] = rhs.pop(m.state)
        t = machines.Transition(lhs, rhs)
        g.add_edge(q, r, {'label': t})
    return g


