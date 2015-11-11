import collections
import six
from . import syntax
from .syntax import START, ACCEPT, REJECT, BLANK

class Store(object):
    """A (configuration of a) store, which could be a tape, stack, or
       state. It consists of a string together with a head
       position."""

    def __init__(self, values=None, position=None):
        from .readers import string_to_store
        self.position = 0
        if values is None:
            self.values = []
        elif isinstance(values, six.string_types):
            other = string_to_store(values)
            self.values = other.values
            self.position = other.position
        else:
            self.values = list(values)
        if position is not None:
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
    def __init__(self, *args):
        from .readers import string_to_transition
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, six.string_types):
                arg = string_to_transition(arg)
                self.lhs = arg.lhs
                self.rhs = arg.rhs
            else:
                raise TypeError("can't construct Transition from {}".format(type(arg)))
        elif len(args) == 2:
            lhs, rhs = args
            self.lhs = tuple(Store(x) for x in lhs)
            self.rhs = tuple(Store(x) for x in rhs)

        else:
            raise TypeError("invalid arguments to Transition")

    def match(self, stores):
        if len(self.lhs) != len(stores):
            raise ValueError()
        for x, store in zip(self.lhs, stores):
            i = store.position - x.position
            if i < 0:
                return False
            n = len(x)
            while i+n > len(store) and x[n-1] == BLANK:
                n -= 1
            if store.values[i:i+n] != x.values[:n]:
                return False
        return True

    def apply(self, stores):
        stores = tuple(store.copy() for store in stores)

        for x, y, store in zip(self.lhs, self.rhs, stores):
            i = store.position - x.position
            if i < 0:
                raise ValueError("transition cannot apply")
            n = len(x)
            while i+n > len(store) and x[n-1] == BLANK:
                store.values.append(BLANK)
            if store.values[i:i+n] != x.values:
                raise ValueError("transition cannot apply")
            store.values[i:i+n] = y.values
            store.position = i + y.position

            # don't move off left end
            store.position = max(0, store.position)

            # pad or clip the store
            while len(store) <= store.position-1:
                store.values.append(BLANK)
            while len(store)-1 > store.position and store[-1] == BLANK:
                store.values[-1:] = []

        return stores

    def __str__(self):
        return "%s -> %s" % (",".join(map(str, self.lhs)), 
                             ",".join(map(str, self.rhs)))

class Machine(object):
    def __init__(self, num_stores, input=None):
        self.transitions = []
        self.num_stores = num_stores
        self.input = input

        self.start_config = None
        self.accept_configs = set()
        self.reject_configs = set()

    def set_start_config(self, config):
        # If input is missing, supply &
        if self.input is not None and len(config) == self.num_stores-1:
            config = list(config)
            config[self.input:self.input] = [[]]
        # since there is no Configuration object, make a fake Transition
        t = Transition([[]]*self.num_stores, config)
        self.start_config = t.rhs

    def add_accept_config(self, config):
        # If input is missing, supply _. This is meant for machines
        # with one-way inputs.
        if self.input is not None and len(config) == self.num_stores-1:
            config = list(config)
            config[self.input:self.input] = [[BLANK]]
        # since there is no Configuration object, make a fake Transition
        t = Transition(config, [[]]*self.num_stores)
        self.accept_configs.add(t.lhs)

    def add_reject_config(self, config):
        # If input is missing, supply _. This is meant for machines
        # with one-way inputs.
        if self.input is not None and len(config) == self.num_stores-1:
            config = list(config)
            config[self.input:self.input] = [[BLANK]]
        # since there is no Configuration object, make a fake Transition
        t = Transition(config, [[]]*self.num_stores)
        self.reject_configs.add(t.lhs)

    def add_transition(self, *args):
        if len(args) == 1 and isinstance(args[0], Transition):
            t = args[0]
        else:
            t = Transition(*args)

        # If input is missing on the rhs, fill in &
        if self.input is not None and len(t.rhs) == self.num_stores-1:
            t.rhs = list(t.rhs)
            t.rhs[self.input:self.input] = [Store()]
            t.rhs = tuple(t.rhs)

        if len(t.lhs) != self.num_stores:
            raise TypeError("wrong number of stores on left-hand side")
        if len(t.rhs) != self.num_stores:
            raise TypeError("wrong number of stores on right-hand side")

        self.transitions.append(t)

    def get_transitions(self):
        one_way_input = self.has_input(self.input)
        for t in self.transitions:
            if one_way_input:
                rhs = list(t.rhs)
                del rhs[self.input]
                t = Transition(t.lhs, rhs)
            yield t

    def __str__(self):
        return "\n".join(str(t) for t in self.get_transitions())

    def _ipython_display_(self):
        from IPython.display import display
        from .writers import display_graph
        display(display_graph(self))

    def run(self, input_string, trace=False):
        # Breadth-first search
        agenda = collections.deque()
        chart = set()

        # Initial configuration
        input_tokens = syntax.lexer(input_string)
        config = list(self.start_config)
        config[self.input] = Store(input_tokens)
        config = tuple(config)
                  
        agenda.append(config)
        run = Run(self)

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
                    agenda.append(nconfig)

        return run

    ### Testing for different types of automata

    def has_cell(self, s):
        """Tests whether store `s` is a cell, that is, it uses exactly one
        cell, and there can take on only a finite number of states)."""

        for t in self.transitions:
            if len(t.lhs[s]) != 1:
                return False
            if len(t.rhs[s]) != 1:
                return False
            if t.lhs[s].position != 0:
                return False
            if t.rhs[s].position != 0:
                return False
        return True

    def has_input(self, s):
        """Tests whether store `s` is an input, that is, it only deletes and
        never moves from position 0."""

        for t in self.transitions:
            if t.lhs[s].position != 0:
                return False
            if len(t.rhs[s]) != 0:
                return False
        return True

    def has_output(self, s):
        """Tests whether store `s` is an output, that is, it only appends and
        is always one past the end."""

        for t in self.transitions:
            if len(t.lhs[s]) != 0:
                return False
            if t.rhs[s].position != len(t.rhs[s]):
                return False
        return True

    def has_stack(self, s):
        """Tests whether store `s` is a stack, that is, it never moves from
        position 0."""
        for t in self.transitions:
            if t.lhs[s].position != 0:
                return False
            if t.rhs[s].position != 0:
                return False
        return True

    def has_readonly(self, s):
        """Tests whether store `s` is read-only."""
        for t in self.transitions:
            if list(t.lhs[s]) != list(t.rhs[s]):
                return False
        return True

    def is_finite(self):
        """Tests whether machine is finite state, in a broad sense.
        It should have one input and any number of cells."""
        cells = set()
        lhs = set()
        for s in range(self.num_stores):
            if self.has_cell(s):
                cells.add(s)
            if self.has_input(s):
                lhs.add(s)
        # It's possible to be both a cell and an input,
        # and we just need to check that there is some way to 
        # designate exactly 1 stack and num_store-1 cells
        return (len(cells|lhs) == self.num_stores and 
                len(lhs) >= 1 and 
                len(cells) >= self.num_stores-1)

    def is_pushdown(self):
        """Tests whether machine is a pushdown automaton, in a broad sense.
        It should have one input and one stack, and any number of cells."""
        cells = set()
        lhs = set()
        stacks = set()
        for s in range(self.num_stores):
            if self.has_cell(s):
                cells.add(s)
            if self.has_input(s):
                lhs.add(s)
            if self.has_stack(s):
                stacks.add(s)
        return (len(cells|lhs|stacks) == self.num_stores and
                len(lhs) >= 1 and
                len(cells) >= self.num_stores-2)

    def is_deterministic(self):
        """Tests whether machine is deterministic."""
        # naive quadratic algorithm
        for i, t1 in enumerate(self.transitions):
            for t2 in self.transitions[:i]:
                match = True
                for in1, in2 in zip(t1.lhs, t2.lhs):
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
    def __init__(self, machine):
        self.machine = machine
        self.configs = set()
        self.edges = set()

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
            # Rank nodes by input position
            l = len([x for x in config[self.machine.input] if x != BLANK])
            return (-l, config[1])

        result = []
        result.append("digraph {")
        result.append("  rankdir=TB;")
        result.append('  node [fontname=Courier,fontsize=10,shape=box,style=rounded,height=0,width=0,margin="0.055,0.042"];')
        result.append("  edge [arrowhead=vee,arrowsize=0.5];")

        one_way_input = self.machine.has_input(self.machine.input)

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
        
