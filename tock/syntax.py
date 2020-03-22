import re
from . import settings

BLANK = '_'

class Tokens(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def __str__(self):
        return " ".join(self.tokens[:self.pos]) + " ^ " + " ".join(self.tokens[self.pos:])

    def __getitem__(self, index):
        return self.tokens[index]

    def __len__(self):
        return len(self.tokens)

    @property
    def cur(self):
        return self.tokens[self.pos]
    @property
    def next(self):
        return self.tokens[self.pos+1]

whitespace_re = re.compile(r"\s*(//.*)?")

# Symbols can be |- -| # $ or any string of alphanumerics or _ .
symbol_re = re.compile(r"\|-|-\||#|\$|[A-Za-z0-9_.]+")
class Symbol(str):
    def _repr_html_(self):
        return self

# Operators
operator_re = re.compile(r"->|[&^(){},@>|*]")
class Operator(str):
    pass

def lexer(s):
    i = 0
    tokens = []
    m = whitespace_re.match(s, i)
    if m:
        i = m.end()
    while i < len(s):
        m = symbol_re.match(s, i)
        if m:
            token = Symbol(m.group())
        else:
            m = operator_re.match(s, i)
            if m:
                token = Operator(m.group())
            else:
                raise ValueError("couldn't understand input: %s" % s[i:])
        tokens.append(token)
        i = m.end()
        m = whitespace_re.match(s, i)
        if m:
            i = m.end()
    return Tokens(tokens)

def parse_character(s, c):
    if s.pos == len(s):
        raise ValueError("expected %s, found end of string" % c)
    elif s.cur != c:
        raise ValueError("expected %s, found %s" % (c, s.c))
    s.pos += 1

def parse_symbol(s):
    if not isinstance(s.cur, Symbol):
        raise ValueError("expected symbol, found %s" % (s.cur))
    else:
        x = s.cur
        s.pos += 1
        return x

def parse_string(s):
    if s.cur == '&':
        s.pos += 1
        return []
    else:
        result = []
        while s.pos < len(s) and isinstance(s.cur, Symbol):
            result.append(s.cur)
            s.pos += 1
        return result

def parse_multiple(s, f, values=None):
    """Parse multiple comma-separated elements, each of which is parsed
       using function f."""
    if values is None: values = []
    values.append(f(s))
    if s.pos < len(s) and s.cur == ',':
        s.pos += 1
        return parse_multiple(s, f, values)
    else:
        return values

def parse_end(s):
    if s.pos < len(s):
        raise ValueError("unexpected %s" % (s.cur))

def parse_store(s):
    from .machines import Store
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
    if settings.display_direction_as == 'alpha':
        if s.pos+1 < len(s) and s.cur == ',':
            if s.next == 'L':
                s.pos += 2
                position = -1
            elif s.next == 'R':
                s.pos += 2
                position = len(x)
    if position is None:
        position = 0
    return Store(x, position)

def parse_tuple(s):
    parse_character(s, '(')
    value = tuple(parse_multiple(s, parse_store))
    parse_character(s, ')')
    return value

def parse_set(s):
    parse_character(s, '{')
    if s.cur == '(':
        value = set(parse_multiple(s, parse_tuple))
    else:
        value = {(x,) for x in parse_multiple(s, parse_store)}
    parse_character(s, '}')
    return value

def string_to_state(s):
    """s is a string possibly preceded by > or @."""
    s = lexer(s)
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
    x = parse_symbol(s)
    parse_end(s)
    return x, attrs

def string_to_store(s):
    s = lexer(s)
    x = parse_store(s)
    parse_end(s)
    return x

def string_to_config(s):
    """s is a comma-separated list of stores."""
    from .machines import Configuration
    s = lexer(s)
    x = parse_multiple(s, parse_store)
    parse_end(s)
    return Configuration(x)

def string_to_configs(s):
    """s is a string in one of the following formats:
       - x,y
       - (x,y)
       - {x,y}
       - {(w,x),(y,z)}
       In any case, returns a set of tuples of stores.
    """

    s = lexer(s)
    value = None
    if s.pos == len(s):
        value = set()
    elif s.cur == '{':
        value = parse_set(s)
    elif s.cur == '(':
        value = {parse_tuple(s)}
    else:
        value = {tuple(parse_multiple(s, parse_store))}
    parse_end(s)

    return value

def string_to_transition(s):
    """s is a string of the form a,b or a,b->c,d"""
    from .machines import Transition
    s = lexer(s)
    lhs = parse_multiple(s, parse_store)
    if s.pos < len(s) and s.cur == "->":
        s.pos += 1
        rhs = parse_multiple(s, parse_store)
    else:
        rhs = ()
    parse_end(s)
    return Transition(lhs, rhs)

