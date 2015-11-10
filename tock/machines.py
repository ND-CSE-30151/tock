import collections
from . import lexer
from .constants import *

class Store(object):
    """A (configuration of a) store, which could be a tape, stack, or
       state. It consists of a string together with a head
       position."""

    def __init__(self, values=None, position=0):
        self.values = list(values) if values is not None else []
        self.position = position

    def copy(self):
        return Store(self.values, self.position)

    def __eq__(self, other):
        return type(other) == Store and self.values == other.values and self.position == other.position
    def __ne__(self, other):
        return not self == other
    def __hash__(self):
        return hash((tuple(self.values), self.position))

    def __lt__(self, other):
        return self.values < other.values

    def __len__(self):
        return len(self.values)
    def __getitem__(self, i):
        return self.values[i]
    def __setitem__(self, i, x):
        self.values[i] = x

    def __repr__(self):
        if self.position == 0:
            return "Store(%s)" % (repr(" ".join(self.values)),)
        else:
            return "Store(%s, %s)" % (repr(" ".join(self.values)), self.position)
    def __str__(self):
        if len(self) == 0:
            if self.position == 0:
                return "&"
            elif self.position == -1:
                return "^ &"
            else:
                raise ValueError()

        elif len(self) == 1 and self.position == 0:
            return self.values[0]

        result = []
        if self.position == -1:
            result.append("^")
        for i, x in enumerate(self.values):
            if i == self.position:
                result.append("[%s]" % (x,))
            else:
                result.append(str(x))
        if self.position == len(self.values):
            result.append("^")
        return " ".join(result)

class Transition(object):
    def __init__(self, inputs, outputs):
        self.inputs = tuple(inputs)
        self.outputs = tuple(outputs)

    def match(self, stores):
        if len(self.inputs) != len(stores):
            raise ValueError()
        for input, store in zip(self.inputs, stores):
            i = store.position - input.position
            if i < 0:
                return False
            l = len(input)
            while i+l > len(store) and input[l-1] == BLANK:
                l -= 1
            if store.values[i:i+l] != input.values[:l]:
                return False
        return True

    def apply(self, stores):
        stores = tuple(store.copy() for store in stores)

        for input, output, store in zip(self.inputs, self.outputs, stores):
            i = store.position - input.position
            if i < 0:
                raise ValueError("transition cannot apply")
            l = len(input)
            while i+l > len(store) and input[l-1] == BLANK:
                store.values.append(BLANK)
            if store.values[i:i+l] != input.values:
                raise ValueError("transition cannot apply")
            store.values[i:i+l] = output.values
            store.position = i + output.position

            # don't move off left end
            store.position = max(0, store.position)

            # pad or clip the store
            while len(store) <= store.position-1:
                store.values.append(BLANK)
            while len(store)-1 > store.position and store[-1] == BLANK:
                store.values[-1:] = []

        return stores

    def __str__(self):
        return "%s -> %s" % (",".join(map(str, self.inputs)), 
                             ",".join(map(str, self.outputs)))

class Machine(object):
    def __init__(self):
        self.transitions = []
        self.num_stores = None

    def add_transition(self, t):
        if self.num_stores is None:
            self.num_stores = len(t.inputs)
        else:
            if len(t.inputs) != self.num_stores:
                raise TypeError("wrong number of conditions")
            if len(t.outputs) != self.num_stores:
                raise TypeError("wrong number of actions")
        self.transitions.append(t)

    def __str__(self):
        return "\n".join(str(t) for t in self.transitions)

    def _ipython_display_(self):
        from IPython.display import display
        from .writers import display_graph
        display(display_graph(self))

    def run(self, input_string, trace=False):
        # Breadth-first search
        agenda = collections.deque()
        chart = set()

        # Initial configuration
        input_tokens = lexer.lexer(input_string)
        config = (Store([START]), Store(input_tokens, 0)) + tuple(Store() for s in range(2, self.num_stores))
        agenda.append(config)
        run = Run(self, config)

        while len(agenda) > 0:
            tconfig = agenda.popleft()

            if trace: print("trigger: {}".format(tconfig))

            for rule in self.transitions:
                if trace: print("rule: {}".format(rule))
                if rule.match(tconfig):
                    nconfig = rule.apply(tconfig)

                    if nconfig in chart:
                        if trace: print("merge: {}".format(nconfig))
                    else:
                        chart.add(nconfig)
                        if trace: print("add: {}".format(nconfig))
                    run.add(tconfig, nconfig)
                    #if nconfig[0].values[0] == ACCEPT:
                    #    return run
                    agenda.append(nconfig)

        return run

    ### Testing for different types of automata

    def has_cell(self, s):
        """Tests whether store `s` is a cell, that is, it uses exactly one
        cell, and there can take on only a finite number of states)."""

        for t in self.transitions:
            if len(t.inputs[s]) != 1:
                return False
            if len(t.outputs[s]) != 1:
                return False
            if t.inputs[s].position != 0:
                return False
            if t.outputs[s].position != 0:
                return False
        return True

    def has_input(self, s):
        """Tests whether store `s` is an input, that is, it only deletes and
        never moves from position 0."""

        for t in self.transitions:
            if t.inputs[s].position != 0:
                return False
            if len(t.outputs[s]) != 0:
                return False
        return True

    def has_output(self, s):
        """Tests whether store `s` is an output, that is, it only appends and
        is always one past the end."""

        for t in self.transitions:
            if len(t.inputs[s]) != 0:
                return False
            if t.outputs[s].position != len(t.outputs[s]):
                return False
        return True

    def has_stack(self, s):
        """Tests whether store `s` is a stack, that is, it never moves from
        position 0."""
        for t in self.transitions:
            if t.inputs[s].position != 0:
                return False
            if t.outputs[s].position != 0:
                return False
        return True

    def has_readonly(self, s):
        """Tests whether store `s` is read-only."""
        for t in self.transitions:
            if list(t.inputs[s]) != list(t.outputs[s]):
                return False
        return True

    def is_finite(self):
        """Tests whether machine is finite state, in a broad sense.
        It should have one input and any number of cells."""
        cells = set()
        inputs = set()
        for s in range(self.num_stores):
            if self.has_cell(s):
                cells.add(s)
            if self.has_input(s):
                inputs.add(s)
        # It's possible to be both a cell and an input,
        # and we just need to check that there is some way to 
        # designate exactly 1 stack and num_store-1 cells
        return (len(cells|inputs) == self.num_stores and 
                len(inputs) >= 1 and 
                len(cells) >= self.num_stores-1)

    def is_pushdown(self):
        """Tests whether machine is a pushdown automaton, in a broad sense.
        It should have one input and one stack, and any number of cells."""
        cells = set()
        inputs = set()
        stacks = set()
        for s in range(self.num_stores):
            if self.has_cell(s):
                cells.add(s)
            if self.has_input(s):
                inputs.add(s)
            if self.has_stack(s):
                stacks.add(s)
        return (len(cells|inputs|stacks) == self.num_stores and
                len(inputs) >= 1 and
                len(cells) >= self.num_stores-2)

    def is_deterministic(self):
        """Tests whether machine is deterministic."""
        # naive quadratic algorithm
        for i, t1 in enumerate(self.transitions):
            for t2 in self.transitions[:i]:
                match = True
                for in1, in2 in zip(t1.inputs, t2.inputs):
                    i = max(-in1.position, -in2.position)
                    while i+in1.position < len(in1) and i+in2.position < len(in2):
                        x1 = in1.values[i+in1.position]
                        x2 = in2.values[i+in2.position]
                        if x1 != x2:
                            match = False
                        i += 1
                if match:
                    return False
        return True

def ascii_to_html(s):
    s = str(s)
    s = s.replace("&", "&epsilon;")
    s = s.replace("->", "&rarr;")
    s = s.replace(">", "&gt;")
    return s

class Run(object):
    def __init__(self, machine, start):
        self.machine = machine
        self.configs = set()
        self.edges = set()
        self.start = start
        self.configs.add(start)

    def add(self, from_config, to_config):
        self.configs.add(from_config)
        self.configs.add(to_config)
        self.edges.add((from_config, to_config))

    def _ipython_display_(self):
        def label(config): 
            # Label nodes by config
            return ascii_to_html(','.join(map(str, (config[0][0],) + config[1:])))
        def label_no_input(config): 
            # Label nodes by config sans input (second store)
            return ascii_to_html(','.join(map(str, (config[0][0],) + config[2:])))
        def rank(config): 
            # Rank nodes by input (second store) position
            l = len([x for x in config[1] if x != BLANK])
            return (-l, config[1])

        result = []
        result.append("digraph {")
        result.append("  rankdir=TB;")
        result.append('  node [fontname=Courier,fontsize=10,shape=box,style=rounded,height=0,width=0,margin="0.055,0.042"];')
        result.append("  edge [arrowhead=vee,arrowsize=0.5];")

        one_way_input = self.machine.has_input(1)

        # assign an id to each config
        config_id = {}
        for config in self.configs:
            if config not in config_id:
                config_id[config] = len(config_id)

        for config in self.configs:
            if one_way_input:
                result.append('  %s[label=<%s>];' % (config_id[config], label_no_input(config)))
            else:
                result.append('  %s[label=<%s>];' % (config_id[config], label(config)))
        for from_config, to_config in self.edges:
            result.append("  %s -> %s;" % (config_id[from_config], config_id[to_config]))

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
        
