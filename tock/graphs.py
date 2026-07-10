import collections
import html
import textwrap
from . import machines
from . import syntax

try:
    import anywidget
    import traitlets
except ImportError:
    anywidget = None
    traitlets = None

__all__ = ['Graph', 'from_graph', 'write_dot', 'read_tgf', 'to_graph', 'apply_graph_to_machine', 'Editor']

class Graph:
    """A directed graph. Both nodes and edges can have a ``dict`` of attributes.

    Nodes can be any object that implements ``__hash__`` and ``__eq__``.

    If ``g`` is a ``Graph`` and ``v`` is a node, its attributes can be
    accessed as ``g.nodes[v]``. If ``u`` and ``v`` are nodes, edge ``(u, v)``'s
    attributes can be accessed as ``g.edges[u][v]``.
    """
    def __init__(self, attrs=None):
        self.nodes = {}
        self.edges = {}
        if attrs is None: attrs = {}
        self.attrs = attrs

    def add_node(self, v, attrs=None):
        """Add node ``v`` to the graph with attributes ``attrs``."""
        if attrs is None: attrs = {}
        if v in self.nodes:
            self.nodes[v].update(attrs)
        else:
            self.nodes[v] = attrs

    def remove_node(self, v):
        """Remove node ``v`` and any edges incident to it."""
        del self.nodes[v]
        del self.edges[v]
        for u in self.nodes:
            if u in self.edges and v in self.edges[u]:
                del self.edges[u][v]

    def add_edge(self, u, v, attrs=None):
        """Add an edge from ``u`` to ``v`` with attributes ``attrs``."""
        if attrs is None: attrs = {}
        if u not in self.nodes: self.nodes[u] = {}
        if v not in self.nodes: self.nodes[v] = {}
        self.edges.setdefault(u, {})
        self.edges[u].setdefault(v, [])
        self.edges[u][v].append(attrs)

    def has_edge(self, u, v):
        """Return ``True`` iff there is at least one edge from ``u`` to ``v``."""
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
            raise ValueError("There must be exactly one start node")

        nodes = []
        edges = []
        [v] = start
        while True:
            nodes.append(v)
            u = v
            vs = self.edges.get(u, ())
            if len(vs) == 0:
                break
            elif len(vs) > 1:
                raise ValueError("There must be exactly one path")
            [v] = vs
            if len(self.edges[u][v]) != 1:
                raise ValueError("There must be exactly one path")
            [e] = self.edges[u][v]
            edges.append(e)

        return Path(nodes, edges, self.nodes[v].get('accept', False))

    def shortest_path(self):
        """Finds the shortest path from the start node to an accept node. If
        there is more than one, chooses one arbitrarily."""

        start = [v for v in self.nodes if self.nodes[v].get('start', False)]
        if len(start) != 1:
            raise ValueError("There must be exactly one start node")
        frontier = collections.deque(start)
        pred = {start[0]: None}
        while len(frontier) > 0:
            u = frontier.popleft()
            if self.nodes[u].get('accept', False):
                nodes = []
                edges = []
                while u is not None:
                    nodes.append(u)
                    if pred[u] is not None:
                        edges.append(self.edges[pred[u]][u][0])
                    u = pred[u]
                nodes.reverse()
                edges.reverse()
                return Path(nodes, edges, True)
            for v in self.edges.get(u, ()):
                if v not in pred:
                    frontier.append(v)
                    pred[v] = u
        raise ValueError("There is no accepting path")

    def has_path(self):
        """Return ``True`` iff there is a path from the start node to an accept node."""
        try:
            self.shortest_path()
            return True
        except:
            return False

    def __getitem__(self, u):
        return self.edges[u]

    def _repr_dot_(self, index=None):
        def repr_html(x):
            if hasattr(x, '_repr_html_'):
                return x._repr_html_()
            else:
                return html.escape(str(x), quote=False).replace('\n', '<br/>')
            
        result = []
        result.append('digraph {')
        for key, val in self.attrs.items():
            result.append('  {}={};'.format(key, val))
        result.append('  node [fontname=Monospace,fontsize=10,shape=box,style=rounded,height=0,width=0,margin="0.055,0.042"];')
        result.append('  edge [arrowhead=vee,arrowsize=0.5,fontname=Monospace,fontsize=9];')

        # Draw nodes
        result.append('  _START[shape=none,label=""];\n')
        if index is None:
            index = {}
        else:
            if not isinstance(index, dict):
                raise TypeError('index must be a dict')
            index.clear()
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
        node_has_constraint = set()  # Initialize to handle case when len(has_rank) == 0
        rank_has_constraint = set()
        for v in self.nodes:
            if 'rank' in self.nodes[v]:
                has_rank.add(v)
                rank = self.nodes[v]['rank']
                rank_nodes[rank].add(v)

        if len(has_rank) > 0:
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
                edges = []
                for e in self.edges[u][v]:
                    attrs = {}
                    for key, val in e.items():
                        if key == 'label':
                            attrs['label'] = repr_html(e['label'])
                        elif key in ['style', 'color']:
                            attrs[key] = val
                    edges.append(attrs)

                attrs = {}
                labels = []
                for e in edges:
                    if 'label' in e:
                        labels.append(e['label'])
                    # In principle it's possible for parallel edges to have
                    # different attributes, but not for the cases where
                    # we currently use attributes.
                    attrs.update(e)
                if labels:
                    labels = [f'<tr><td>{label}</td></tr>' for label in labels]
                    attrs['label'] = '<<table border="0" cellpadding="1">{}</table>>'.format(''.join(labels))
                edges = [attrs]

                for attrs in edges:
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
        from IPython.display import display # type: ignore
        from .graphviz import run_dot
        display(run_dot(self._repr_dot_()))

def graph_to_json(g):
    j = {'nodes': {}, 'edges': {}}
    for attr in ['xmin', 'xmax', 'ymin', 'ymax']:
        if attr in g.attrs:
            j[attr] = g.attrs[attr]
    for v in g.nodes:
        j['nodes'][v] = {}
        for attr in ['start', 'accept', 'x', 'y', 'startx', 'starty']:
            if attr in g.nodes[v]:
                j['nodes'][str(v)][attr] = g.nodes[v][attr]
    for u in g.edges:
        j['edges'][u] = {}
        for v in g.edges[u]:
            j['edges'][u][v] = []
            for e in g.edges[u][v]:
                attrs = {'label': str(e['label'])}
                for attr in ['anchorx', 'anchory']:
                    if attr in e:
                        attrs[attr] = e[attr]
                j['edges'][u][v].append(attrs)
    return j

def json_to_graph(j):
    g = Graph()
    for v in j['nodes']:
        g.add_node(str(v), {
            'start': j['nodes'][v].get('start', False),
            'accept': j['nodes'][v].get('accept', False)})
    for u in j['edges']:
        for v in j['edges'][u]:
            for e in j['edges'][u][v]:
                g.add_edge(u, v,
                           {'label': syntax.str_to_transition(e['label'])})
    return g

def read_tgf(filename):
    """Reads a file in Trivial Graph Format. Edge labels are read into the
    ``label`` attribute."""
    with open(filename) as file:
        g = Graph()

        states = {}
        section = 0

        for line in file:
            line = line.strip()
            if line == "": 
                continue
            fields = line.split()

            if fields == ["#"]:
                section += 1
            elif section == 0:
                # Nodes
                if len(fields) != 2:
                    raise ValueError(f"A node must have an id and a label (not {line})")
                i, q = fields
                q, attrs = syntax.str_to_state(q)
                states[i] = q
                g.add_node(q, attrs)

            elif section == 1:
                # Edges
                if len(fields) != 3:
                    raise ValueError(f"An edge must have a tail, a head, and a label (not {line})")
                i, j, t = fields
                q, r = states[i], states[j]
                t = syntax.str_to_transition(t)
                g.add_edge(q, r, {'label':t})
    return from_graph(g)

def from_graph(g):
    """Convert a ``Graph`` ``g`` to a ``Machine``."""
    transitions = []

    for q in g.edges:
        for r in g.edges[q]:
            for e in g.edges[q][r]:
                t = e['label']
                transitions.append(([[q]]+list(t.lhs), [[r]]+list(t.rhs)))

    start_state = None
    accept_states = set()
    for q in g.nodes:
        if g.nodes[q].get('start', False):
            if start_state is not None:
                raise ValueError("A Machine must have only one start state")
            start_state = q
        if g.nodes[q].get('accept', False):
            accept_states.add(q)
    if start_state is None:
        raise ValueError("A Machine must have one start state")

    return machines.from_transitions(transitions, start_state, accept_states)

def apply_graph_to_machine(m, g):
    """Replace machine ``m`` with the contents of graph ``g``."""
    m.transitions = []
    for q in g.edges:
        for r in g.edges[q]:
            for e in g.edges[q][r]:
                t = e['label']
                lhs = list(t.lhs)
                lhs[m.state:m.state] = [q]
                rhs = list(t.rhs)
                rhs[m.state:m.state] = [r]
                try:
                    m.add_transition(lhs, rhs)
                except Exception as e:
                    raise ValueError(f"In transition from {q} on {t} to {r}: {e}") from None

    start_state = None
    accept_states = set()
    for q in g.nodes:
        if g.nodes[q].get('start', False):
            if start_state is not None:
                raise ValueError("A Machine must have only one start state")
            start_state = q
        if g.nodes[q].get('accept', False):
            accept_states.add(q)
    if start_state is None:
        raise ValueError("A Machine must have one start state")
    m.set_start_state(start_state)
    m.accept_configs.clear()
    m.add_accept_states(accept_states)

def write_dot(x, filename):
    """Write a ``Machine`` or ``Graph`` ``x`` to file ``filename`` in GraphViz
    (DOT) format."""
    if isinstance(x, machines.Machine):
        x = to_graph(x)
    if not isinstance(x, Graph):
        raise TypeError("Only Machines and Graphs can be written as DOT files")
    with open(filename, "w") as file:
        file.write(x._repr_dot_())

def to_graph(m):
    """Convert a ``Machine`` ``m`` to a ``Graph``."""
    g = Graph()
    g.attrs['rankdir'] = 'LR'
    try:
        q = m.get_start_state()
        g.add_node(q, {'start': True})
    except ValueError:
        pass
    for q in m.get_accept_states():
        g.add_node(q, {'accept': True})
    for t in m.get_transitions():
        state = t[m.state]
        [[q]] = state.lhs
        [[r]] = state.rhs
        
        t = t[:m.state] + t[m.state+1:]
        g.add_edge(q, r, {'label': t})
    return g

class Path:
    def __init__(self, nodes, edges, accept):
        self.nodes = nodes
        self.edges = edges
        self.accept = accept

    def __len__(self):
        return len(self.nodes)
    def __getitem__(self, i):
        return self.nodes[i]

    def __str__(self):
        return '\n'.join(map(str, self.nodes))
    def _repr_html_(self):
        html = ['<table style="font-family: Monospace, monospace;">\n']
        for config in self.nodes:
            if not isinstance(config, machines.Configuration):
                raise TypeError('A Path can only displayed as HTML if its nodes are Configurations')
            html.append('  <tr>')
            for store in config.stores:
                html.extend(['<td style="text-align: left">', store._repr_html_(), '</td>'])
            html.append('</tr>\n')
        html.append('</table>\n')
        if self.accept:
            html.append('<p>accept</p>')
        else:
            html.append('<p>reject</p>')
        return ''.join(html)

def layout(g):
    try:
        import pydot
    except ImportError as e:
        raise ImportError("pydot is required for graph layout. Reinstall tock or run 'pip install pydot'.") from e
    from .graphviz import run_dot

    def parse_string(s):
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
            s = s.replace('\\\n','')
        return s
    
    node_index = {}
    dot = g._repr_dot_(index=node_index)
    dot_str: str = run_dot(dot, format="dot")  # type: ignore
    dot_str = dot_str.replace('#', '&#35;') # workaround for https://github.com/pydot/pydot/issues/235
    dot_list = pydot.graph_from_dot_data(dot_str)
    dot = dot_list[0] if dot_list else None  # type: ignore
    if dot is None:
        raise ValueError("Failed to parse dot data")

    bb_string = dot.get_bb()  # type: ignore
    if bb_string is None:
        # dot -Tdot relocates bb="..." into graph[bb="..."] (a bug?)
        for attrs in dot.get_graph_defaults():  # type: ignore
            if 'bb' in attrs:
                bb_string = attrs['bb']
    bbox = parse_string(bb_string).split(',')
    g.attrs['xmin'] = float(bbox[0])
    g.attrs['ymin'] = float(bbox[1])
    g.attrs['xmax'] = float(bbox[2])
    g.attrs['ymax'] = float(bbox[3])

    for v in g.nodes:
        vid = node_index[v]
        vdot = dot.get_node(str(vid))[0]  # type: ignore
        pos = parse_string(vdot.get_attributes()['pos'])
        x, y = pos.split(',', 1)
        g.nodes[v]['x'] = float(x)
        g.nodes[v]['y'] = float(y)
        if g.nodes[v].get('start', False):
            sdot = dot.get_node('_START')[0]  # type: ignore
            pos = parse_string(sdot.get_attributes()['pos'])
            x, y = pos.split(',', 1)
            g.nodes[v]['startx'] = float(x)
            g.nodes[v]['starty'] = float(y)
        
    for u in g.edges:
        uid = node_index[u]
        for v in g.edges[u]:
            vid = node_index[v]
            [edot] = dot.get_edge(str(uid), str(vid)) # we merged parallel edges, so there must be exactly one
            
            pos = parse_string(edot.get_attributes()['pos'])
            points = []
            start = end = None
            for pstr in pos.split():
                fields = pstr.split(',')
                if fields[0] not in ['s', 'e']:
                    points.append(tuple(map(float, fields)))
            if len(points) % 2 == 1:
                # Every third point is actually on the curve.
                # Choose the middle one.
                anchor = (points[len(points)//2][0],
                          points[len(points)//2][1])
            else:
                # Find the middle of the middle spline
                i = len(points)//2-2
                anchor = ((points[i][0] + points[i+1][0]*3 + points[i+2][0]*3 + points[i+3][0])/8,
                          (points[i][1] + points[i+1][1]*3 + points[i+2][1]*3 + points[i+3][1])/8)
            for e in g.edges[u][v]:
                e['anchorx'], e['anchory'] = anchor
    return g

def _editor_widget_esm():
    import importlib.resources

    if __package__ is None:
        raise RuntimeError("__package__ is not defined")
    src = importlib.resources.read_text(__package__, 'editor.js')
    src = textwrap.indent(src, '    ')
    return (
        "function createTockEditorRuntime() {\n"
        f"{src}\n"
        "    return { main };\n"
        "}\n\n"
        "function makeAnywidgetBackend(model) {\n"
        "    let requestNonce = 0;\n"
        "    const loadHandlers = [];\n"
        "    const statusHandlers = [];\n"
        "\n"
        "    model.on('change:editor_graph', () => {\n"
        "        const graph = model.get('editor_graph');\n"
        "        for (const handler of loadHandlers)\n"
        "            handler(graph);\n"
        "    });\n"
        "\n"
        "    model.on('change:editor_status', () => {\n"
        "        const status = model.get('editor_status');\n"
        "        for (const handler of statusHandlers)\n"
        "            handler(status);\n"
        "    });\n"
        "\n"
        "    function sendRequest(kind, graph) {\n"
        "        requestNonce += 1;\n"
        "        const request = { kind, nonce: requestNonce };\n"
        "        if (graph !== undefined)\n"
        "            request.graph = graph;\n"
        "        model.set('editor_request', request);\n"
        "        model.save_changes();\n"
        "    }\n"
        "\n"
        "    return {\n"
        "        load() {\n"
        "            sendRequest('load');\n"
        "        },\n"
        "        save(graph) {\n"
        "            sendRequest('save', graph);\n"
        "        },\n"
        "        onLoad(handler) {\n"
        "            loadHandlers.push(handler);\n"
        "        },\n"
        "        onStatus(handler) {\n"
        "            statusHandlers.push(handler);\n"
        "        },\n"
        "        initialGraph() {\n"
        "            return model.get('editor_graph');\n"
        "        },\n"
        "    };\n"
        "}\n\n"
        "function render({ model, el }) {\n"
        "    const runtime = createTockEditorRuntime();\n"
        "    return runtime.main(0, { element: el, backend: makeAnywidgetBackend(model) });\n"
        "}\n\n"
        "export default { render };\n"
    )


class _EditorBase:
    _editors = []

    def __init__(self, m, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.m = m
        self.editor_index = len(type(self)._editors)
        type(self)._editors.append(self)

    def save(self, j):
        g = json_to_graph(j)
        apply_graph_to_machine(self.m, g)

    def load(self):
        g = to_graph(self.m)
        layout(g)
        return graph_to_json(g)


if anywidget is not None and traitlets is not None:
    class Editor(_EditorBase, anywidget.AnyWidget):  # type: ignore
        _editors = []
        _esm = _editor_widget_esm()
        editor_graph = traitlets.Dict(default_value={}).tag(sync=True)  # type: ignore
        editor_request = traitlets.Dict(default_value={}).tag(sync=True)  # type: ignore
        editor_status = traitlets.Unicode('').tag(sync=True)  # type: ignore

        def __init__(self, m):
            self._last_request_nonce = None
            super().__init__(m)
            self.observe(self._handle_request, names='editor_request')
            self.editor_graph = self.load()

        def _handle_request(self, change):
            request = change['new']
            if not request:
                return

            nonce = request.get('nonce')
            if nonce is None or nonce == self._last_request_nonce:
                return
            self._last_request_nonce = nonce

            kind = request.get('kind')
            try:
                if kind == 'save':
                    self.save(request.get('graph'))
                    self.editor_status = 'Save successful'
                elif kind == 'load':
                    self.editor_graph = self.load()
                    self.editor_status = ''
                else:
                    self.editor_status = f'Unknown editor request: {kind}'
            except Exception as e:
                self.editor_status = str(e)
else:
    class Editor(_EditorBase):  # type: ignore
        _editors = []

        def __init__(self, m):
            super().__init__(m)

            import importlib.resources
            if __package__ is None:
                raise RuntimeError("__package__ is not defined")
            self.src = importlib.resources.read_text(__package__, 'editor.js')
            self.src = self.src + f'main({self.editor_index});'

            try:
                import google.colab  # type: ignore
                import IPython.display  # type: ignore
                google.colab.output.register_callback('notebook.editor_load',
                                                      lambda ei: IPython.display.JSON(editor_load(ei)))
                google.colab.output.register_callback('notebook.editor_save', editor_save)
            except ImportError:
                pass

        def _ipython_display_(self):
            # bad to have more than one of these per Editor object?
            from IPython.display import display, Javascript  # type: ignore
            display(Javascript(self.src))

def editor_save(ei, g):
    Editor._editors[ei].save(g)
    
def editor_load(ei):
    return Editor._editors[ei].load()
