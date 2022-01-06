"""This module contains Tock's main data structure, the Machine class,
and associated classes and functions."""

import collections
import itertools
import dataclasses
from . import syntax, settings

__all__ = ['Machine',
           'FiniteAutomaton', 'PushdownAutomaton', 'TuringMachine',
           'BASE', 'STREAM', 'TAPE']

@dataclasses.dataclass(frozen=True, order=True)
class Store(syntax.String):
    """A string together with a head position. It is used either as a
    store of a Machine or as a pattern to be matched against a store of a
    Machine.

    Arguments:
        values: Sequence of Symbols
        position (int): The head position, between -1 and len(values)
        store (Store or str): Another Store to copy, or a str to convert to a Store
    """

    position: int #: The head position

    def __init__(self, *args):
        if len(args) == 0:
            values = []
            position = 0
        elif len(args) == 1:
            if isinstance(args[0], Store):
                values = args[0].values
                position = args[0].position
            elif isinstance(args[0], str):
                other = syntax.str_to_store(args[0])
                values = other.values
                position = other.position
            else:
                values = tuple(args[0])
                position = 0
        elif len(args) == 2:
            values = args[0]
            position = args[1]
        else:
            raise TypeError("invalid arguments to Store")
            
        syntax.String.__init__(self, values)
        object.__setattr__(self, 'position',
                           position if position is not None else default_position)

    def __str__(self):
        if len(self) == 0:
            if self.position in [0, None]:
                return "ε"
            elif self.position == -1:
                return "^ ε"
            else:
                raise ValueError(f"Position {self.position} out of range")

        # Special case to avoid printing states as [q]
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
        result = " ".join(result)

        return result

    def _repr_html_(self):
        return str(self)

    def match(self, other):
        """Returns true iff `self` (as a pattern) matches `other` (as a
        store). Note that this is asymmetric: `other` is allowed
        to have symbols that aren't found in `self`."""

        i = other.position - self.position
        if i < 0:
            return False
        n = len(self)
        while i+n > len(other) and self[n-1] == syntax.BLANK:
            n -= 1
        if other.values[i:i+n] != self.values[:n]:
            return False
        return True
    
@dataclasses.dataclass(frozen=True, order=True)
class Configuration:
    """A configuration, which is essentially a tuple of `Stores`.

    Arguments:
        stores: A tuple of Stores
        config (Configuration or str): Another Configuration to copy, or a str to convert to a Configuration
    """
    
    stores: tuple #: A tuple of Stores
    
    def __init__(self, arg):
        if isinstance(arg, Configuration):
            stores = arg.stores
        elif isinstance(arg, str):
            stores = syntax.str_to_config(arg).stores
        elif isinstance(arg, (list, tuple)):
            stores = tuple(x if isinstance(x, Store) else Store(x) for x in arg)
        else:
            raise TypeError("Can't construct Configuration from {}".format(type(arg)))
        object.__setattr__(self, 'stores', stores)

    def __str__(self):
        return ','.join(map(str, self.stores))
    def _repr_html_(self):
        return ','.join(s._repr_html_() for s in self.stores)

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
            if not s1.match(s2):
                return False
        return True

@dataclasses.dataclass(frozen=True, order=True)
class Transition:
    """A transition from one `Configuration` to another `Configuration`.

    Arguments:
        lhs (Configuration): left-hand side
        rhs (Configuration): right-hand side
        transition (Transition or str): Another Transition to copy, or a str to convert to a Transition
    """

    lhs: Configuration #: left-hand side Configuration
    rhs: Configuration #: right-hand side Configuration
    
    def __init__(self, *args):
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, Transition):
                lhs = arg.lhs
                rhs = arg.rhs
            elif isinstance(arg, str):
                arg = syntax.str_to_transition(arg)
                lhs = arg.lhs
                rhs = arg.rhs
            else:
                raise TypeError(f"Can't construct Transition from an object of type {type(arg)}")
        elif len(args) == 2:
            lhs, rhs = args
            lhs = Configuration(lhs)
            rhs = Configuration(rhs)
        else:
            raise TypeError("Invalid arguments to Transition")
        object.__setattr__(self, 'lhs', lhs)
        object.__setattr__(self, 'rhs', rhs)

    def match(self, config):
        """Returns True iff self can be applied to config."""
        return self.lhs.match(config)

    def apply(self, config):
        stores = []

        for x, y, store in zip(self.lhs, self.rhs, config):
            values = list(store.values)
            position = store.position
            
            i = position - x.position
            if i < 0:
                raise ValueError("Transition cannot apply")
            n = len(x)
            # Pad store with blanks to fit x
            while i+n > len(values) and x[len(values)-i] == syntax.BLANK:
                values.append(syntax.BLANK)
            if tuple(values[i:i+n]) != x.values:
                raise ValueError("Transition cannot apply")
            values[i:i+n] = y.values
            position = i + y.position

            # Don't move off left end
            position = max(0, position)

            # Pad store with blanks,
            # unless store is empty (so don't pad the empty stack)
            while position > 0 and len(values)-1 < position:
                values.append(syntax.BLANK)

            stores.append(Store(values, position))

        return Configuration(stores)

    def __str__(self):
        if len(self.rhs) > 0:
            return "{} → {}".format(self.lhs, self.rhs)
        else:
            return str(self.lhs)

    def _repr_html_(self):
        if len(self.rhs) > 0:
            return "{} &rarr; {}".format(self.lhs._repr_html_(), self.rhs._repr_html_())
        else:
            return self.lhs._repr_html_()

@dataclasses.dataclass(frozen=True, order=True)
class AlignedTransition(Transition):
    """A `Transition` that has an alignment between the lhs and rhs. These
    are generated by `get_transitions` so that even if the number of
    lhs and rhs stores changes, we can still keep track of their
    relationship to the machine's stores.

    If `t` is an `AlignedTransition`, `t[i]` is a `Transition`
    containing the lhs and rhs just for store number `i`.
    """

    transitions: tuple
    
    def __init__(self, transitions):
        object.__setattr__(self, 'transitions', tuple(Transition(t) for t in transitions))

    @staticmethod
    def _flatten(lol):
        return list(itertools.chain(*lol))

    @property
    def lhs(self):
        return Configuration(self._flatten([t.lhs for t in self.transitions]))
    @property
    def rhs(self):
        return Configuration(self._flatten([t.rhs for t in self.transitions]))

    def __len__(self):
        return len(self.transitions)
    def __getitem__(self, i):
        if isinstance(i, slice):
            return AlignedTransition(self.transitions[i])
        else:
            return self.transitions[i]
    def __add__(self, other):
        return AlignedTransition(self.transitions+other.transitions)

# Store types.
    
BASE = "BASE"
STREAM = "STREAM"
TAPE = "TAPE"

# Define some standard automaton types.

def FiniteAutomaton():
    """A (deterministic or nondeterministic) finite automaton."""
    return Machine([BASE, STREAM], state=0, input=1)
def PushdownAutomaton():
    """A (deterministic or nondeterministic) pushdown automaton."""
    return Machine([BASE, STREAM, BASE], state=0, input=1)
def TuringMachine():
    """A (deterministic or nondeterministic) Turing machine."""
    return Machine([BASE, TAPE], state=0, input=1)

class Machine:
    """A machine (automaton) that accepts or rejects strings. It has one
    or more stores, which can act as states, stacks, tapes, etc. When
    it is run on a string, the stores are initialized to a start
    configuration and rewritten by transitions until an accept
    configuration is reached or no more rewrites are possible.

    Arguments:

        store_types: A list of store types, one for each
          store. Allowed types are `BASE`, `STREAM`, and `TAPE`. See
          `add_transition` and `add_accept_state` for explanation of
          these types.
        state (int): The index of the store which is the state. The state
          is usually what distinguishes the start and accept
          configurations, and it is also treated specially when
          reading/writing machines.
        input (int): The index of the store which is the input store. When
          the machine is run on a string, the input store is initialized
          to the string.
    """
    def __init__(self, store_types, state=None, input=None):
        self.transitions = []                 #: List of transitions
        self.store_types = tuple(store_types) #: Tuple of store types, one for each store
        self.state = state                    #: Which store is the state
        self.input = input                    #: Which store is the input

        self.start_config = None              #: The start configuration
        self.accept_configs = set()           #: Set of accept configurations

    @property
    def num_stores(self):
        """How many stores the Machine has."""
        return len(self.store_types)

    def get_start_state(self):
        """Return the start state."""
        if self.state is None: raise ValueError("This Machine doesn't have a state")
        if self.start_config is None: raise ValueError("This Machine doesn't have a start state")
        [q] = self.start_config[self.state]
        return q

    def set_start_state(self, q):
        """Set the start configuration with `q` as the start state. The input
        store will be initialized to the input string, and all other
        stores will be initialized to the empty string.
        """
        config = [[]] * self.num_stores
        if self.state is None:
            raise ValueError("This Machine doesn't have a state")
        config[self.state] = [q]
        self.start_config = Configuration(config)

    def add_accept_state(self, q):
        """Add an accept configuration with `q` as the state. Any stores with
        type STREAM must reach the end of the string in order to
        accept. All other stores will not have any accepting
        conditions.
        """
        config = [[]] * self.num_stores

        if self.state is None: raise ValueError("This Machine doesn't have a state")
        config[self.state] = [q]

        if self.input is not None and self.store_types[self.input] == STREAM:
            # Machine must be at end of input to accept
            config[self.input] = [syntax.BLANK]

        self.accept_configs.add(Configuration(config))

    def add_accept_states(self, qs):
        """Add a list of accept states (see `add_accept_state`)."""
        for q in qs:
            self.add_accept_state(q)

    def get_accept_states(self):
        """Return the set of accept states."""
        if self.state is None: raise ValueError("This Machine doesn't have a state")
        states = set()
        for config in self.accept_configs:
            [q] = config[self.state]
            states.add(q)
        return states
        
    @property
    def states(self):
        """The set of all possible states."""
        if self.state is None: raise ValueError("This Machine doesn't have a state")
        return (set(t.lhs[self.state][0] for t in self.transitions) | 
                set(t.rhs[self.state][0] for t in self.transitions))

    def add_transition(self, *args):
        """Add a transition. The argument can either be a `Transition` or a
        left-hand side and a right-hand side.

        - If a store is a STREAM, there should not be an rhs; an empty
          rhs is automatically inserted.
        - If a store is a TAPE, there should be two rhs's: a write
          (whose position is ignored) and a move (L or R).
        """
        if len(args) == 1 and isinstance(args[0], Transition):
            t = args[0]
        else:
            t = Transition(*args)

        lhs = []
        rhs = []
        li = ri = 0
        for si, st in enumerate(self.store_types):
            if st == BASE:
                if li >= len(t.lhs):
                    raise TypeError("Too few things on left-hand side of arrow")
                if ri >= len(t.rhs):
                    raise TypeError("Too few things on right-hand side of arrow")
                lhs.append(t.lhs[li])
                rhs.append(t.rhs[ri])
                li += 1
                ri += 1
            elif st == STREAM:
                if li >= len(t.lhs):
                    raise TypeError("Too few things on left-hand side of arrow")
                lhs.append(t.lhs[li])
                li += 1
                rhs.append(Store())
            elif st == TAPE:
                if li >= len(t.lhs):
                    raise TypeError("Too few things on left-hand side of arrow")
                if ri+1 >= len(t.rhs):
                    raise TypeError("Too few things on right-hand side of arrow")
                lhs.append(t.lhs[li])
                b, [d] = t.rhs[ri:ri+2]
                if d == 'L':
                    p = -1
                elif d == 'S':
                    p = 0
                elif d == 'R':
                    p = len(b)
                else:
                    raise ValueError('Invalid move {} (allowed moves are L, S, and R)'.format(repr(d)))
                rhs.append(Store(b, p))
                li += 1
                ri += 2
            else:
                assert False

        if li < len(t.lhs):
            raise TypeError("Too many things on left-hand side of arrow")
        if ri < len(t.rhs):
            raise TypeError("Too many things on right-hand side of arrow")
        if len(lhs) != len(rhs):
            raise TypeError("Left-hand side and right-hand side must have same number of stores")

        self.transitions.append(Transition(lhs, rhs))

    def add_transitions(self, transitions):
        """Add a list of transitions (see `add_transition`)."""
        for t in transitions:
            self.add_transition(t)

    def get_transitions(self):
        """Return an iterator over all transitions, as AlignedTransitions.

        - For any stores of type STREAM, the generated
          transitions do not have an rhs for the input.

        - For any stores of type TAPE, the generated transitions will
          have an additional field to indicate a move (L or R).
        """
        for t in self.transitions:
            ts = []
            for si, st in enumerate(self.store_types):
                if st == BASE:
                    ts.append(Transition([t.lhs[si]], [t.rhs[si]]))
                elif st == STREAM:
                    assert len(t.rhs[si]) == 0
                    ts.append(Transition([t.lhs[si]], []))
                elif st == TAPE:
                    b = t.rhs[si].values
                    if t.rhs[si].position == -1:
                        d = 'L'
                    elif t.rhs[si].position == 0:
                        d = 'S'
                    elif t.rhs[si].position == len(b):
                        d = 'R'
                    else:
                        raise ValueError('No move for length {} and position {}'.format(len(b), t.rhs[si].position))
                    ts.append(Transition([t.lhs[si]], [b, d]))
                else:
                    assert False
            yield AlignedTransition(ts)

    def __str__(self):
        return "\n".join(str(t) for t in self.get_transitions())

    def _ipython_display_(self):
        from IPython.display import display # type: ignore
        from .graphs import to_graph
        display(to_graph(self))

    def edit(self):
        """In a Jupyter notebook, returns a visual editor for this Machine."""
        from .graphs import Editor
        return Editor(self)

    ### Testing for different types of automata

    def has_stack(self, s):
        """Tests whether store `s` is a stack, that is, it never moves from
        position 0.
        """
        if self.start_config[s].position != 0:
            return False
        for t in self.transitions:
            if not t.lhs[s].position == t.rhs[s].position == 0:
                return False
        for c in self.accept_configs:
            if c[s].position != 0:
                return False
        return True

    def has_cell(self, s):
        """Tests whether store `s` uses exactly one cell, and therefore can
        take on only a finite number of states.
        """
        if not self.has_stack(s):
            return False
        for t in self.transitions:
            if not len(t.lhs[s]) == len(t.rhs[s]) == 1:
                return False
        return True

    def has_input_stream(self, s):
        """Tests whether store `s` is an input stream, that is, it only
        deletes and never moves from position 0.
        """
        if not self.has_stack(s):
            return False
        for t in self.transitions:
            if len(t.rhs[s]) != 0:
                return False
        for c in self.accept_configs:
            if any(x != syntax.BLANK for x in c[s]):
                return False
        return True

    def has_tape(self, s):
        """Tests whether store `s` is a tape, that is, it never inserts or
        deletes symbols."""
        for t in self.transitions:
            if len(t.lhs[s]) != len(t.rhs[s]):
                return False
        return True

    def has_readonly(self, s):
        """Tests whether store `s` is read-only."""
        for t in self.transitions:
            if t.lhs[s].values != t.rhs[s].values:
                return False
        return True

    def is_finite(self):
        """Tests whether machine is a finite automaton."""
        return (self.store_types == (BASE, STREAM) and
                self.state == 0 and self.has_cell(0) and
                self.input == 1 and self.has_input_stream(1))

    def is_pushdown(self):
        """Tests whether machine is a pushdown automaton."""
        return (self.store_types == (BASE, STREAM, BASE) and
                self.state == 0 and self.has_cell(0) and
                self.input == 1 and self.has_input_stream(1) and
                self.has_stack(2))

    def is_turing(self):
        """Tests whether machine is a Turing machine."""
        return (self.store_types == (BASE, TAPE) and
                self.state == 0 and self.has_cell(0) and
                self.input == 1 and self.has_tape(1))

    def is_deterministic(self, verbose=False):
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
                    if verbose:
                        print('conflicting transitions:')
                        print(' ', t1)
                        print(' ', t2)
                    return False
        return True

def from_transitions(transitions, start_state, accept_states):
    """Create a `Machine` from transitions (in the same format returned by
    `get_transitions`), trying to guess what kind of machine is intended.
    
    - Store 0 is the state.
    - Store 1 is the input.
    - Whether a store is a TAPE is guessed based on whether the next
      field only ever has values of L or R.
    - Whether the input is a STREAM is guessed based on the size
      of the right-hand sides of the transitions.

    Not really meant to be used directly; used by `from_graph` and `from_table`.
    """

    lhs_sizes = set()
    rhs_sizes = set()
    for lhs, rhs in transitions:
        lhs_sizes.add(len(lhs))
        rhs_sizes.add(len(rhs))
            
    if len(lhs_sizes) != 1:
        raise ValueError('All left-hand sides must have the same size')
    [lhs_size] = lhs_sizes
    if len(rhs_sizes) != 1:
        raise ValueError('All right-hand sides must have the same size')
    [rhs_size] = rhs_sizes

    store_types = []

    rhs_vocab = [set() for si in range(rhs_size)]
    for lhs, rhs in transitions:
        for si, x in enumerate(rhs):
            rhs_vocab[si].update(rhs[si])
            
    for si in range(lhs_size):
        if si+1 < rhs_size and len(rhs_vocab[si+1]) > 0 and rhs_vocab[si+1].issubset({'L', 'S', 'R'}):
            store_types.append(TAPE)
            rhs_size -= 1
            del rhs_vocab[si+1]
        else:
            store_types.append(BASE)
            
    if lhs_size == rhs_size:
        pass
    elif lhs_size-1 == rhs_size:
        store_types[1] = STREAM
    else:
        raise ValueError("Right-hand sides must either be same size or one smaller than left-hand sides")

    m = Machine(store_types, state=0, input=1)

    m.set_start_state(start_state)
    m.add_accept_states(accept_states)

    for lhs, rhs in transitions:
        m.add_transition(lhs, rhs)

    return m
