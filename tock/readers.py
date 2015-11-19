from . import machines
from . import syntax

# This module has three parts:
# - Parser for transitions and pieces of transitions (maybe should move to syntax.py and/or machines.py)
# - Reader for TGF files (maybe should move to graphs.py)

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
    attrs = {}
    while True:
        if s.cur == '>':
            attrs['start'] = True
            s.pos += 1
        elif s.cur == '@':
            attrs['accept'] = True
            s.pos += 1
        else:
            break
    x = syntax.parse_symbol(s)
    syntax.parse_end(s)
    return x, attrs

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
