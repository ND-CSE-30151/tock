import csv
import six

from . import machines
from . import lexer
from . import special
from .constants import *

__all__ = ['read_csv', 'read_tgf']

### Parser for transitions and pieces of transitions

def parse_string(s):
    if s.cur == '&':
        s.pos += 1
        return []
    else:
        result = []
        while s.pos < len(s) and isinstance(s.cur, lexer.Symbol):
            result.append(s.cur)
            s.pos += 1
        return result

def parse_store(s):
    position = None
    if s.cur == '^':
        s.pos += 1
        position = -1
    x = parse_string(s)
    if s.pos < len(s) and s.cur == '^':
        s.pos += 1
        if position is not None:
            raise ValueError("head is only allowed to be in one position")
        position = len(x)
    if position is None:
        position = 0
    return machines.Store(x, position)

def parse_multiple(s, f, values=None):
    if values is None: values = []
    values.append(f(s))
    if s.pos < len(s) and s.cur == ',':
        s.pos += 1
        return parse_multiple(s, f, values)
    else:
        return values

def parse_tuple(s):
    lexer.parse_character(s, '(')
    value = tuple(parse_multiple(s, parse_store))
    lexer.parse_character(s, ')')
    return value

def parse_set(s):
    lexer.parse_character(s, '{')
    if s.cur == '(':
        value = set(parse_multiple(s, parse_tuple))
    else:
        value = {(x,) for x in parse_multiple(s, parse_store)}
    lexer.parse_character(s, '}')
    return value

def string_to_state(s):
    """s is a string possibly preceded by > or @."""
    s = lexer.lexer(s)
    flags = set()
    while True:
        if s.cur in '>@':
            flags.add(s.cur)
            s.pos += 1
        else:
            break
    x = lexer.parse_symbol(s)
    lexer.parse_end(s)
    return x, flags

def string_to_config(s):
    """s is a comma-separated list of stores."""
    s = lexer.lexer(s)
    x = parse_multiple(s, parse_store)
    lexer.parse_end(s)
    return tuple(x)

def string_to_configs(s):
    """s is a string in one of the following formats:
       - x,y
       - (x,y)
       - {x,y}
       - {(w,x),(y,z)}
       In any case, returns a set of tuples of stores.
    """

    s = lexer.lexer(s)
    value = None
    if s.pos == len(s):
        value = set()
    elif s.cur == '{':
        value = parse_set(s)
    elif s.cur == '(':
        value = {parse_tuple(s)}
    else:
        value = {tuple(parse_multiple(s, parse_store))}
    lexer.parse_end(s)

    return value

def string_to_transition(s):
    """s is a string of the form a,b or a,b->c,d"""
    s = lexer.lexer(s)
    lhs = parse_multiple(s, parse_store)
    if s.pos+2 < len(s) and s[s.pos:s.pos+2] == "->":
        s.pos += 2
        rhs = parse_multiple(s, parse_store)
    else:
        rhs = ()
    lexer.parse_end(s)
    return tuple(lhs), tuple(rhs)

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
        m = machines.Machine()
        n = single_value(map(len, lhs))+1

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
                special.set_initial_state(m, q, n)
            if '@' in flags:
                special.add_final_state(m, q, n)

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
                l = (machines.Store([q]),) + l
                for r in rs:
                    special.add_transition(m, l, r)
            i += 1
    return m

def read_tgf(infilename):
    """Reads a file in Trivial Graph Format."""

    with open(infilename) as infile:
        states = {}
        flags = {}
        m = machines.Machine()

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
            lhs, rhs = string_to_transition(t)
            lhs = (machines.Store([q]),) + lhs
            rhs = (machines.Store([r]),) + rhs
            special.add_transition(m, lhs, rhs)

        for i in states:
            if '>' in flags[i]:
                special.set_initial_state(m, states[i])
            if '@' in flags[i]:
                special.add_final_state(m, states[i])

    return m

