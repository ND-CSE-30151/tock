import collections
import six
from . import syntax

__all__ = ['Machine', 'FiniteAutomaton', 'PushdownAutomaton', 'TuringMachine', 'determinize']

class Store(object):
    """A (configuration of a) store, which could be a tape, stack, or
       state. It consists of a string together with a head
       position."""

    def __init__(self, values=None, position="default"):
        self.position = 0
        if values is None:
            self.values = []
        elif isinstance(values, six.string_types):
            other = syntax.string_to_store(values)
            self.values = other.values
            self.position = other.position
        else:
            self.values = list(values)
        if position != "default":
            self.position = position

    def deepcopy(self):
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
            return "Store({})".format(repr(self.values))
        else:
            return "Store({}, {})".format(repr(self.values), self.position)
    def __str__(self):
        if len(self) == 0:
            if self.position in [0, None]:
                return "&"
            elif self.position == -1:
                return "^ &"
            else:
                raise ValueError()

        elif len(self) == 1 and self.position == 0:
            return str(self.values[0])

        result = []
        if self.position == -1:
            result.append("^")
        for i, x in enumerate(self.values):
            if i == self.position:
                result.append("[{}]".format(x))
            else:
                result.append(str(x))
        if self.position == len(self.values):
            result.append("^")
        return " ".join(result)

    def _repr_html_(self):
        # nothing fancy
        return str(self).replace('&', '&epsilon;').replace('...', '&hellip;')

class Configuration(object):
    def __init__(self, arg):
        if isinstance(arg, Configuration):
            self.stores = arg.stores
        elif isinstance(arg, six.string_types):
            self.stores = syntax.string_to_config(arg).stores
        elif isinstance(arg, (list, tuple)):
            self.stores = tuple(x if isinstance(x, Store) else Store(x) for x in arg)
        else:
            raise TypeError("can't construct Configuration from {}".format(type(arg)))

    def deepcopy(self):
        return Configuration([s.deepcopy() for s in self.stores])

    def __str__(self):
        return ','.join(map(str, self.stores))
    def _repr_html_(self):
        return ','.join(s._repr_html_() for s in self.stores)

    def __eq__(self, other):
        return self.stores == other.stores
    def __hash__(self):
        return hash(self.stores)

    def __len__(self):
        return len(self.stores)
    def __getitem__(self, i):
        return self.stores[i]

    def match(self, other):
        """Returns true iff self (as a pattern) matches other (as a
        configuration). Note that this is asymmetric: other is allowed
        to have symbols that aren't found in self."""

        if len(self) != len(other):
            raise ValueError()
        for s1, s2 in zip(self, other):
            i = s2.position - s1.position
            if i < 0:
                return False
            n = len(s1)
            while i+n > len(s2) and s1[n-1] == syntax.BLANK:
                n -= 1
            if s2.values[i:i+n] != s1.values[:n]:
                return False
        return True

class Transition(object):
    def __init__(self, *args):
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, six.string_types):
                arg = syntax.string_to_transition(arg)
                self.lhs = arg.lhs
                self.rhs = arg.rhs
            else:
                raise TypeError("can't construct Transition from {}".format(type(arg)))
        elif len(args) == 2:
            lhs, rhs = args
            self.lhs = Configuration(lhs)
            self.rhs = Configuration(rhs)

        else:
            raise TypeError("invalid arguments to Transition")

    def match(self, config):
        """Returns True iff self can be applied to config."""
        return self.lhs.match(config)

    def apply(self, config):
        config = config.deepcopy()

        for x, y, store in zip(self.lhs, self.rhs, config):
            i = store.position - x.position
            if i < 0:
                raise ValueError("transition cannot apply")
            n = len(x)
            while i+n > len(store) and x[n-1] == syntax.BLANK:
                store.values.append(syntax.BLANK)
            if store.values[i:i+n] != x.values:
                raise ValueError("transition cannot apply")
            store.values[i:i+n] = y.values
            store.position = i + y.position

            # don't move off left end
            store.position = max(0, store.position)

            # pad or clip the store
            while len(store) <= store.position-1:
                store.values.append(syntax.BLANK)
            while len(store)-1 > store.position and store[-1] == syntax.BLANK:
                store.values[-1:] = []

        return config

    def __str__(self):
        if len(self.rhs) > 0:
            return "{} -> {}".format(self.lhs, self.rhs)
        else:
            return str(self.lhs)

    def _repr_html_(self):
        if len(self.rhs) > 0:
            return "{} &rarr; {}".format(self.lhs._repr_html_(), self.rhs._repr_html_())
        else:
            return self.lhs._repr_html_()

# Define some standard automaton types.

def FiniteAutomaton(): return Machine(2, state=0, input=1, oneway=True)
def PushdownAutomaton(): return Machine(3, state=0, input=1, oneway=True)
def TuringMachine(): return Machine(2, state=0, input=1)

class Machine(object):
    def __init__(self, num_stores, state=None, input=None, oneway=False):

        """An automaton.
        num_stores: How many stores the machine should have.
        state: Which store is the state; used by set_accept_state and
               add_accept_config.
        input: Which store is the input.
        oneway: Whether the input is consumed from left to right, or
                can be read and written in both directions.
        """

        self.transitions = []
        self.num_stores = num_stores
        self.state = state
        self.input = input
        self.oneway = input is not None and oneway

        self.start_config = None
        self.accept_configs = set()

    def set_start_config(self, config):
        if isinstance(config, six.string_types):
            config = syntax.string_to_config(config)
        # If input is missing, supply &
        if self.oneway:
            config = list(config)
            config[self.input:self.input] = [[]]
            config = Configuration(config)
        self.start_config = config

    def add_accept_config(self, config):
        if self.oneway:
            end = Store([syntax.BLANK])
            s = config[self.input]
            if len(config[self.input]) == 0:
                config = list(config)
                config[self.input] = end
            config = Configuration(config)

            if config[self.input] != end:
                raise ValueError("machine can only accept at end of input")
        else:
            config = Configuration(config)
        self.accept_configs.add(config)

    def add_accept_configs(self, configs):
        for c in configs:
            self.add_accept_config(c)

    def get_start_state(self):
        if self.state is None:
            raise ValueError("no state defined")
        if sum(len(store) for store in self.start_config) != 1:
            raise ValueError("machine does not have a start state")
        [q] = self.start_config[self.state]
        return q

    def set_start_state(self, q):
        config = [[]] * self.num_stores

        if self.state is None: raise ValueError("no state defined")
        config[self.state] = [q]

        self.start_config = Configuration(config)

    def add_accept_state(self, q):
        config = [[]] * self.num_stores

        if self.state is None: raise ValueError("no state defined")
        config[self.state] = [q]

        self.add_accept_config(config)

    def add_accept_states(self, qs):
        for q in qs:
            self.add_accept_state(q)

    def get_accept_states(self):
        if self.state is None: raise ValueError("no state defined")
        # to do: error checking
        return [config[self.state][0] for config in self.accept_configs]
        
    @property
    def states(self):
        if self.state is None: raise ValueError("no state defined")
        return set(t.lhs[self.state][0] for t in self.transitions)

    def add_transition(self, *args):
        if len(args) == 1 and isinstance(args[0], Transition):
            t = args[0]
        else:
            t = Transition(*args)

        # If input is one-way, fill in & for the rhs
        if self.oneway:
            t.rhs = list(t.rhs)
            t.rhs[self.input:self.input] = [Store()]
            t.rhs = Configuration(t.rhs)

        if len(t.lhs) != self.num_stores:
            raise TypeError("wrong number of stores on left-hand side")
        if len(t.rhs) != self.num_stores:
            raise TypeError("wrong number of stores on right-hand side")

        self.transitions.append(t)

    def add_transitions(self, transitions):
        for t in transitions:
            self.add_transition(t)

    def get_transitions(self):
        for t in self.transitions:
            if self.oneway:
                rhs = list(t.rhs)
                del rhs[self.input]
                t = Transition(t.lhs, rhs)
            yield t

    def __str__(self):
        return "\n".join(str(t) for t in self.get_transitions())

    def _ipython_display_(self):
        from IPython.display import display
        from .graphs import to_graph
        display(to_graph(self))

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
        """Tests whether store `s` is a one-way input, that is, it only deletes and
        never moves from position 0."""

        # to do: check start_config
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
        """Tests whether machine is a finite automaton."""
        return (self.num_stores == 2 and
                self.state == 0 and self.has_cell(0) and
                self.input == 1 and self.has_input(1))

    def is_pushdown(self):
        """Tests whether machine is a pushdown automaton."""
        return (self.num_stores == 3 and
                self.state == 0 and self.has_cell(0) and
                self.input == 1 and self.has_input(1) and
                self.has_stack(2))

    def is_deterministic(self):
        """Tests whether machine is deterministic."""
        # naive quadratic algorithm
        patterns = [t.lhs for t in self.transitions] + list(self.accept_configs)
        for i, t1 in enumerate(patterns):
            for t2 in patterns[:i]:
                match = True
                for in1, in2 in zip(t1, t2):
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

def determinize(m):
    """Determinizes a finite automaton."""
    if not m.is_finite():
        raise TypeError("machine must be a finite automaton")

    transitions = collections.defaultdict(lambda: collections.defaultdict(set))
    for transition in m.get_transitions():
        [[lstate], read] = transition.lhs
        [[rstate]] = transition.rhs
        if len(read) > 1:
            raise NotSupportedException("multiple input symbols on transition not supported")
        transitions[lstate][tuple(read)].add(rstate)

    class Set(frozenset):
        def __str__(self):
            return "{{{}}}".format(",".join(map(str, sorted(self))))
        def _repr_html_(self):
            return "{{{}}}".format(",".join(x._repr_html_() for x in sorted(self)))

    def eclosure(states):
        """Find epsilon-closure of set of states"""
        states = set(states)
        frontier = set(states)
        while len(frontier) > 0:
            lstate = frontier.pop()
            for rstate in transitions[lstate][()]:
                if rstate not in states:
                    states.add(rstate)
                    frontier.add(rstate)
        return states

    dm = FiniteAutomaton()

    start_state = Set(eclosure([m.get_start_state()]))
    dm.set_start_state(start_state)

    frontier = {start_state}
    visited = set()
    while len(frontier) > 0:
        lstates = frontier.pop()
        if lstates in visited:
            continue
        visited.add(lstates)
        dtransitions = collections.defaultdict(set)
        for lstate in lstates:
            for read in transitions[lstate]:
                if read != ():
                    dtransitions[read] |= transitions[lstate][read]
        for read in dtransitions:
            rstates = Set(eclosure(dtransitions[read]))
            dm.add_transition([[lstates], read], [[rstates]])
            frontier.add(rstates)

    accept_states = set(m.get_accept_states())
    for states in visited:
        if len(states & accept_states) > 0:
            dm.add_accept_state(states)

    return dm
