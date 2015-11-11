import csv
import six

from . import machines
from . import syntax

__all__ = ['read_csv', 'read_tgf']

# This module has three parts:
# - Parser for transitions and pieces of transitions (maybe should move to syntax.py and/or machines.py)
# - Reader for CSV files (maybe should move to a tables.py)
# - Reader for TGF files (maybe should move to a graphs.py)

### Parser for transitions and pieces of transitions

def parse_store(s):
    position = None
    if s.cur == '^':
        s.pos += 1
        position = -1
    x = syntax.parse_string(s)
    if s.pos < len(s) and s.cur == '^':
        s.pos += 1
        if position is not None:
            raise ValueError("head is only allowed to be in one position")
        position = len(x)
    if position is None:
        position = 0
    return machines.Store(x, position)

def parse_tuple(s):
    syntax.parse_character(s, '(')
    value = tuple(syntax.parse_multiple(s, parse_store))
    syntax.parse_character(s, ')')
    return value

def parse_set(s):
    syntax.parse_character(s, '{')
    if s.cur == '(':
        value = set(syntax.parse_multiple(s, parse_tuple))
    else:
        value = {(x,) for x in syntax.parse_multiple(s, parse_store)}
    syntax.parse_character(s, '}')
    return value

def string_to_state(s):
    """s is a string possibly preceded by > or @."""
    s = syntax.lexer(s)
    flags = set()
    while True:
        if s.cur in '>@':
            flags.add(s.cur)
            s.pos += 1
        else:
            break
    x = syntax.parse_symbol(s)
    syntax.parse_end(s)
    return x, flags

def string_to_store(s):
    s = syntax.lexer(s)
    x = parse_store(s)
    syntax.parse_end(s)
    return x

def string_to_config(s):
    """s is a comma-separated list of stores."""
    s = syntax.lexer(s)
    x = syntax.parse_multiple(s, parse_store)
    syntax.parse_end(s)
    return tuple(x)

def string_to_configs(s):
    """s is a string in one of the following formats:
       - x,y
       - (x,y)
       - {x,y}
       - {(w,x),(y,z)}
       In any case, returns a set of tuples of stores.
    """

    s = syntax.lexer(s)
    value = None
    if s.pos == len(s):
        value = set()
    elif s.cur == '{':
        value = parse_set(s)
    elif s.cur == '(':
        value = {parse_tuple(s)}
    else:
        value = {tuple(syntax.parse_multiple(s, parse_store))}
    syntax.parse_end(s)

    return value

def string_to_transition(s):
    """s is a string of the form a,b or a,b->c,d"""
    s = syntax.lexer(s)
    lhs = syntax.parse_multiple(s, parse_store)
    if s.pos < len(s) and s.cur == "->":
        s.pos += 1
        rhs = syntax.parse_multiple(s, parse_store)
    else:
        rhs = ()
    syntax.parse_end(s)
    return machines.Transition(lhs, rhs)

def single_value(s):
    s = set(s)
    if len(s) != 1:
        raise ValueError()
    return s.pop()

### Top-level functions for reading and writing machines in various formats.

def read_csv(infilename):
    """Reads a CSV file containing a tabular description of a transition function,
       as found in Sipser. Major difference: instead of multiple header rows,
       only a single header row whose entries might be tuples.
       """
    with open(infilename) as infile:

        reader = csv.reader(infile)
        lhs = []
        transitions = []

        # Header row has one dummy cell, and then each cell has lhs values
        # for the input and any additional stores.
        row = six.next(reader)
        lhs = []
        j = 1
        for cell in row[1:]: 
            try:
                lhs.append(string_to_config(cell))
            except Exception as e:
                e.message = "cell %s1: %s" % (chr(ord('A')+j), e.message)
                raise
            j += 1
        num_stores = single_value(map(len, lhs))+1
        m = machines.Machine(num_stores, input=1)

        # Body
        i = 1
        for row in reader:
            if sum(len(cell.strip()) for cell in row) == 0:
                continue
            try:
                q, flags = string_to_state(row[0])
            except Exception as e:
                e.message = "cell A%d: %s" % (i+1, e.message)
                raise
            if '>' in flags:
                m.set_start_config([q] + [[]] * (num_stores-2))
            if '@' in flags:
                m.add_accept_config([q] + [[]] * (num_stores-2))

            rhs = []
            j = 1
            for cell in row[1:]:
                try:
                    rhs.append(string_to_configs(cell))
                except Exception as e:
                    e.message = "cell %s%d: %s" % (chr(ord('A')+j), i+1, e.message)
                    raise
                j += 1
            for l, rs in zip(lhs, rhs):
                l = ([q],) + l
                for r in rs:
                    m.add_transition(l, r)
            i += 1
    return m

def read_tgf(infilename):
    """Reads a file in Trivial Graph Format."""

    with open(infilename) as infile:
        states = {}
        transitions = []
        flags = {}

        # Nodes
        for line in infile:
            line = line.strip()
            if line == "": 
                continue
            elif line == "#":
                break
            i, q = line.split(None, 1)
            states[i], flags[i] = string_to_state(q)

        # Edges
        for line in infile:
            line = line.strip()
            if line == "": 
                continue
            i, j, t = line.split(None, 2)
            q, r = states[i], states[j]
            t = string_to_transition(t)
            transitions.append((([q],)+t.lhs, ([r],)+t.rhs))

    num_stores = single_value(len(lhs) for lhs, rhs in transitions)
    m = machines.Machine(num_stores, input=1)

    for i in states:
        if '>' in flags[i]:
            m.set_start_config([states[i]] + [[]] * (num_stores-2))
        if '@' in flags[i]:
            m.add_accept_config([states[i]] + [[]] * (num_stores-2))

    for lhs, rhs in transitions:
        m.add_transition(lhs, rhs)

    return m

