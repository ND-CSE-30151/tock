import collections
from . import machines
from . import syntax

__all__ = ['to_graph', 'write_dot', 'read_tgf']

class Graph(object):
    def __init__(self, attrs=None):
        self.nodes = {}
        self.edges = {}
        if attrs is None: attrs = {}
        self.attrs = attrs

    def add_node(self, v, attrs=None):
        if attrs is None: attrs = {}
        if v in self.nodes:
            self.nodes[v].update(attrs)
        else:
            self.nodes[v] = attrs

    def remove_node(self, v):
        del self.nodes[v]
        del self.edges[v]
        for u in self.nodes:
            if u in self.edges and v in self.edges[u]:
                del self.edges[u][v]

    def add_edge(self, u, v, attrs=None):
        if attrs is None: attrs = {}
        if u not in self.nodes: self.nodes[u] = {}
        if v not in self.nodes: self.nodes[v] = {}
        self.edges.setdefault(u, {})
        self.edges[u].setdefault(v, [])
        self.edges[u][v].append(attrs)

    def has_edge(self, u, v):
        return u in self.edges and v in self.edges[u] and len(self.edges[u][v]) > 0

    def get_edges(self, u, v):
        self.edges.setdefault(u, {})
        self.edges[u].setdefault(v, [])
        return self.edges[u][v]

    def only_path(self):
        """Finds the only path from the start node. If there is more than one,
        raises ValueError."""
        start = [v for v in self.nodes if self.nodes[v].get('start', False)]
        if len(start) != 1: 
            raise ValueError("graph does not have exactly one start node")

        path = []
        [v] = start
        while True:
            path.append(v)
            u = v
            vs = self.edges.get(u, ())
            if len(vs) == 0:
                break
            elif len(vs) > 1:
                raise ValueError("graph does not have exactly one path")
            [v] = vs

        return machines.Path(path)

    def shortest_path(self):
        """Finds the shortest path from the start node to an accept node. If
        there is more than one, chooses one arbitrarily."""

        start = [v for v in self.nodes if self.nodes[v].get('start', False)]
        if len(start) != 1: raise ValueError("graph does not have exactly one start node")
        frontier = collections.deque(start)
        pred = {start[0]: None}
        while len(frontier) > 0:
            u = frontier.popleft()
            if self.nodes[u].get('accept', False):
                path = []
                while u is not None:
                    path.append(u)
                    u = pred[u]
                path.reverse()
                return machines.Path(path)
            for v in self.edges.get(u, ()):
                if v not in pred:
                    frontier.append(v)
                    pred[v] = u
        raise ValueError("graph does not have an accepting path")

    def has_path(self):
        try:
            self.shortest_path()
            return True
        except:
            return False

    def __getitem__(self, u):
        return self.edges[u]

    def _repr_dot_(self):

        def repr_html(x):
            if hasattr(x, '_repr_html_'):
                return x._repr_html_()
            else:
                return str(x)
            
        result = []
        result.append('digraph {')
        for key, val in self.attrs.items():
            result.append('  {}={};'.format(key, val))
        result.append('  node [fontname=Courier,fontsize=10,shape=box,style=rounded,height=0,width=0,margin="0.055,0.042"];')
        result.append('  edge [arrowhead=vee,arrowsize=0.5,fontname=Courier,fontsize=9];')

        # Draw nodes
        result.append('  _START[shape=none,label=""];\n')
        index = {}
        for i, q in enumerate(sorted(self.nodes, key=id)):
            index[q] = i

            attrs = {}
            for key, val in self.nodes[q].items():
                if key in ['label', 'style']:
                    attrs[key] = val

            if 'label' not in attrs:
                attrs['label'] = q
            attrs['label'] = '<'+repr_html(attrs['label'])+'>'

            if self.nodes[q].get('accept', False):
                attrs['peripheries'] = 2

            attrs = ','.join('{}={}'.format(key, val) for (key, val) in attrs.items())
            result.append('  {}[{}];'.format(i, attrs))

        # Draw edges to nowhere
        for q in self.nodes:
            i = index[q]
            if self.nodes[q].get('start', False):
                result.append('  _START -> {}'.format(i))

            if self.nodes[q].get('incomplete', False):
                result.append('  _DOTS_{}[shape=none,label=""];\n'.format(i))
                result.append('  {} -> _DOTS_{}[dir=none,style=dotted]'.format(i, i))

        # Organize nodes into ranks, if any
        rank_nodes = collections.defaultdict(set)
        has_rank = set()
        for v in self.nodes:
            if 'rank' in self.nodes[v]:
                has_rank.add(v)
                rank = self.nodes[v]['rank']
                rank_nodes[rank].add(v)

        if len(has_rank) > 0:
            for rank in rank_nodes:
                result.append('  {{ rank=same; {} }}'.format(' '.join(str(index[v]) for v in rank_nodes[rank])))

            node_has_constraint = set()
            rank_has_constraint = set()
            for u in has_rank:
                ur = self.nodes[u]['rank']
                for v in self.edges.get(u, ()):
                    if v in has_rank:
                        vr = self.nodes[v]['rank']
                        if ur != vr:
                            if vr not in rank_has_constraint:
                                rank_has_constraint.add(vr)
                            node_has_constraint.add(v)

        # Draw normal edges
        for u in self.edges:
            for v in self.edges[u]:
                attrs = {}

                labels = []
                for e in self.edges[u][v]:
                    for key, val in e.items():
                        if key == 'label':
                            labels.append('<tr><td>{}</td></tr>'.format(repr_html(e['label'])))
                        elif key in ['style', 'color']:
                            attrs[key] = val

                if labels:
                    attrs['label'] = '<<table border="0" cellpadding="1">{}</table>>'.format(''.join(labels))

                # Within-rank edges don't constrain position of v if v's position is already determined
                if 'rank' in self.nodes[u] and 'rank' in self.nodes[v] and self.nodes[u]['rank'] == self.nodes[v]['rank'] and v in node_has_constraint:
                    attrs['constraint'] = 'false'

                if attrs:
                    attrs = ','.join('{}={}'.format(key, val) for key, val in attrs.items())
                    result.append('  {} -> {}[{}];'.format(index[u], index[v], attrs))
                else:
                    result.append('  {} -> {};'.format(index[u], index[v]))
        
        result.append('}')
        return '\n'.join(result)

    def _ipython_display_(self):
        from IPython.display import display
        from .graphviz import run_dot
        display(run_dot(self._repr_dot_()))

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
                transitions.append(([[q]]+list(t.lhs), [[r]]+list(t.rhs)))

    lhs_size = single_value(len(lhs) for lhs, rhs in transitions)
    rhs_size = single_value(len(rhs) for lhs, rhs in transitions)
    if lhs_size == rhs_size:
        num_stores = lhs_size
        oneway = False
    elif lhs_size-1 == rhs_size:
        num_stores = lhs_size
        oneway = True
    else:
        raise ValueError("right-hand sides must either be same size or one smaller than left-hand sides")

    m = machines.Machine(num_stores, state=0, input=1, oneway=oneway)

    for q in g.nodes:
        if g.nodes[q].get('start', False):
            if m.start_config is not None:
                raise ValueError("more than one start state")
            m.set_start_state(q)
        if g.nodes[q].get('accept', False):
            m.add_accept_state(q)
    if m.start_config is None:
        raise ValueError("missing start state")

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
    if m.start_config is not None:
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


