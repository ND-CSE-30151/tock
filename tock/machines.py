import collections
import six
from . import syntax

class Store(object):
    """A (configuration of a) store, which could be a tape, stack, or
       state. It consists of a string together with a head
       position."""

    def __init__(self, values=None, position=None):
        self.position = 0
        if values is None:
            self.values = []
        elif isinstance(values, six.string_types):
            other = syntax.string_to_store(values)
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

    def _repr_html_(self):
        # nothing fancy
        return str(self).replace('&', '&epsilon;').replace('...', '&hellip;')

# not yet consistently used
class Configuration(object):
    def __init__(self, stores):
        self.stores = tuple(stores)

    def __str__(self):
        return str(self.stores)
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
            self.lhs = tuple(x if isinstance(x, Store) else Store(x) for x in lhs)
            self.rhs = tuple(x if isinstance(x, Store) else Store(x) for x in rhs)

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
            while i+n > len(store) and x[n-1] == syntax.BLANK:
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

        return stores

    def __str__(self):
        if len(self.rhs) > 0:
            return "%s -> %s" % (",".join(map(str, self.lhs)), 
                                 ",".join(map(str, self.rhs)))
        else:
            return ",".join(map(str, self.lhs))

    def _repr_html_(self):
        if len(self.rhs) > 0:
            return "%s &rarr; %s" % (",".join(s._repr_html_() for s in self.lhs), 
                                 ",".join(s._repr_html_() for s in self.rhs))
        else:
            return ",".join(s._repr_html_() for s in self.lhs)

class Machine(object):
    def __init__(self, num_stores, state=None, input=None):
        self.transitions = []
        self.num_stores = num_stores
        self.state = state
        self.input = input

        self.start_config = None
        self.accept_configs = set()

    def set_start_config(self, config):
        if isinstance(config, six.string_types):
            config = syntax.string_to_config(config)
        # If input is missing, supply &
        if self.input is not None and len(config) == self.num_stores-1:
            config = list(config)
            config[self.input:self.input] = [[]]
        # Since there is no Configuration object, make a fake Transition
        t = Transition([[]]*self.num_stores, config)
        self.start_config = t.rhs

    def add_accept_config(self, config):
        if isinstance(config, six.string_types):
            config = syntax.string_to_config(config)
        # Since there is no Configuration object, make a fake Transition
        t = Transition(config, [[]]*self.num_stores)
        self.accept_configs.add(t.lhs)

    def set_start_state(self, q):
        if self.state is None: raise ValueError("no state defined")
        config = [[]] * self.num_stores
        config[self.state] = q
        self.set_start_config(config)

    def add_accept_state(self, q):
        if self.state is None: raise ValueError("no state defined")
        config = [[]] * self.num_stores
        config[self.state] = q
        if self.input is not None: # and self.has_input(self.input):
            config[self.input] = [syntax.BLANK]
        self.add_accept_config(config)

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
        one_way_input = self.input is not None and self.has_input(self.input)
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

