from . import machines

__all__ = ['display_graph', 'to_graph']

def display_graph(m):
    to_graph(m)._ipython_display_()

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

    def _ipython_display_(self):
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

        from IPython.display import display
        from .viz import viz
        display(viz('\n'.join(result)))

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


