import collections
from . import machines

__all__ = ['to_graph', 'write_dot', 'read_tgf']

class Graph(object):
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.attrs = {}

    def add_node(self, v, attrs=None):
        if attrs is None: attrs = {}
        if v in self.nodes:
            self.nodes[v].update(attrs)
        else:
            self.nodes[v] = attrs

    def add_edge(self, u, v, attrs=None):
        if attrs is None: attrs = {}
        if u not in self.nodes: self.nodes[u] = {}
        if v not in self.nodes: self.nodes[v] = {}
        self.edges.setdefault(u, {})
        self.edges[u].setdefault(v, [])
        self.edges[u][v].append(attrs)

    def __getitem__(self, u):
        return self.edges[u]

    def _repr_dot_(self):

        def repr_html(x):
            try:
                return x._repr_html_()
            except:
                return str(x)
            
        result = []
        result.append('digraph {')
        for key, val in self.attrs.items():
            result.append('  {}={};'.format(key, val))
        result.append('  node [fontname=Courier,fontsize=10,shape=box,style=rounded,height=0,width=0,margin="0.055,0.042"];')
        result.append('  edge [arrowhead=vee,arrowsize=0.5,fontname=Courier,fontsize=9];')

        # Only show nodes that have edges
        nodes = set()
        for u in self.edges:
            nodes.add(u)
            for v in self.edges[u]:
                nodes.add(v)

        # Draw nodes
        index = {}
        for i, q in enumerate(sorted(nodes)):
            index[q] = i

            if 'label' in self.nodes[q]:
                label = self.nodes[q]['label']
            else:
                label = q

            label = repr_html(label)

            if self.nodes[q].get('accept', False):
                result.append('  {}[label="{}",peripheries=2];'.format(i, label))
            else:
                result.append('  {}[label="{}"];'.format(i, label))

        # Draw edges to nowhere
        for q in nodes:
            i = index[q]
            if self.nodes[q].get('start', False):
                result.append('  START[shape=none,label=""];\n')
                result.append('  START -> {}'.format(i))

            if self.nodes[q].get('incomplete', False):
                result.append('  DOTS_{}[shape=none,label=""];\n'.format(i))
                result.append('  {} -> DOTS_{}[dir=none,style=dotted]'.format(i, i))

        # Organize nodes into ranks, if any
        rank_nodes = collections.defaultdict(set)
        has_rank = set()
        for v in nodes:
            if 'rank' in self.nodes[v]:
                has_rank.add(v)
                rank = self.nodes[v]['rank']
                rank_nodes[rank].add(v)

        if len(has_rank) > 0:
            # For each rank, horizontally align nodes and rank label
            rank_index = {}
            for i, rank in enumerate(rank_nodes):
                rank_index[rank] = i
                result.append('  rank{}[shape=plaintext,label=<{}>];'.format(i, repr_html(rank)))
                result.append('  {{ rank=same; rank{} {} }}'.format(i, ' '.join(str(index[v]) for v in rank_nodes[rank])))

            node_has_constraint = set()
            rank_has_constraint = set()
            for u in has_rank:
                ur = self.nodes[u]['rank']
                for v in self.edges.get(u, ()):
                    if v in has_rank:
                        vr = self.nodes[v]['rank']
                        if ur != vr:
                            if vr not in rank_has_constraint:
                                # Align rank label
                                result.append('  rank{} -> rank{}[style=invis];'.format(rank_index[ur], rank_index[vr]))
                                rank_has_constraint.add(vr)
                            node_has_constraint.add(v)

        # Draw normal edges
        for u in self.edges:
            for v in self.edges[u]:
                attrs = {}

                labels = []
                for e in self.edges[u][v]:
                    if 'label' in e:
                        labels.append('<tr><td>{}</td></tr>'.format(e['label']._repr_html_()))
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


