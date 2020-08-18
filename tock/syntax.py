import re
import dataclasses
from . import settings

class Tokens:
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

def repr_html(x):
    if hasattr(x, '_repr_html_'):
        return x._repr_html_()
    else:
        return str(x)

# Symbols can be |- -| # $ or any string of alphanumerics or ' _ .
symbol_re = re.compile(r"\|-|-\||[⊢⊣#$¢␣]|[A-Za-z0-9_.']+")
symbol_mappings = {'|-': '⊢', '-|': '⊣', '_': '␣'}
class Symbol(str):
    def __new__(cls, s):
        s = symbol_mappings.get(s, s)
        return str.__new__(cls, s)
    def _repr_html_(self):
        return self
BLANK = Symbol('_')

# Operators
operator_re = re.compile(r"->|[→&ε^(){},@>|∅∪*]")
operator_mappings = {
    '->': '→',
    '&': 'ε',
    '|': '∪'
}
class Operator(str):
    def __new__(cls, s):
        s = operator_mappings.get(s, s)
        return str.__new__(cls, s)
ARROW = Operator('->')
EPSILON = Operator('&')
EMPTYSET = Operator('∅')

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
                raise ValueError(f"couldn't understand input: {s[i:]}")
        tokens.append(token)
        i = m.end()
        m = whitespace_re.match(s, i)
        if m:
            i = m.end()
    return Tokens(tokens)

def parse_character(s, c):
    if s.pos == len(s):
        raise ValueError(f"expected {c}, found end of string")
    elif s.cur != c:
        raise ValueError(f"expected {c}, found {s.c}")
    s.pos += 1

def parse_symbol(s):
    if not isinstance(s.cur, Symbol):
        raise ValueError(f"expected symbol, found {s.cur}")
    else:
        x = s.cur
        s.pos += 1
        return x

def parse_string(s):
    if s.cur == EPSILON:
        s.pos += 1
        return []
    else:
        result = []
        while s.pos < len(s) and isinstance(s.cur, Symbol):
            result.append(s.cur)
            s.pos += 1
        return result

def parse_multiple(s, f, values=None):
    """Parse one or more comma-separated elements, each of which is parsed
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
        raise ValueError(f"unexpected {s.cur}")

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

def str_to_state(s):
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

def str_to_string(s):
    s = lexer(s)
    x = parse_string(s)
    parse_end(s)
    return x

def str_to_store(s):
    s = lexer(s)
    x = parse_store(s)
    parse_end(s)
    return x

def str_to_config(s):
    """s is a comma-separated list of stores."""
    from .machines import Configuration
    s = lexer(s)
    x = parse_multiple(s, parse_store)
    parse_end(s)
    return Configuration(x)

def str_to_configs(s):
    """Convert str `s` in one of the following formats to a set of tuples of Stores:
       - {(w,x),(y,z)} -> {(w,x),(y,z)}
       - x,y -> {(x, y)}
       - (x,y) -> {(x, y)}
       - {x,y} -> {(x,), (y,)}
       - empty, ∅, or {} -> set()
    """

    s = lexer(s)
    value = None
    if s.pos == len(s):
        value = set()
    elif s.cur == EMPTYSET:
        parse_character(s, EMPTYSET)
        value = set()
    elif s.cur == '{':
        value = parse_set(s)
    elif s.cur == '(':
        value = {parse_tuple(s)}
    else:
        value = {tuple(parse_multiple(s, parse_store))}
    parse_end(s)

    return value

def configs_to_str(configs):
    """Converts a set of Configurations to a str. The inverse of str_to_configs."""
    if len(configs) == 0:
        return ""
    if len(configs) == 1:
        [config] = configs
        return ','.join(map(str, config))
    strings = []
    for config in sorted(configs):
        if len(config) == 1:
            [store] = config
            strings.append(str(store))
        else:
            strings.append('(' + ','.join(map(str, config)) + ')')
    return '{' + ','.join(strings) + '}'

def str_to_transition(s):
    """s is a string of the form a,b or a,b->c,d"""
    from .machines import Transition
    s = lexer(s)
    lhs = parse_multiple(s, parse_store)
    if s.pos < len(s) and s.cur == ARROW:
        s.pos += 1
        rhs = parse_multiple(s, parse_store)
    else:
        rhs = ()
    parse_end(s)
    return Transition(lhs, rhs)

### Data structures that print more like in math books

@dataclasses.dataclass(frozen=True, order=True)
class String:
    """A sequence of `Symbols` (not to be confused with `str`)."""

    values: tuple #: A sequence of Symbols
    
    def __init__(self, values=None):
        if values is None:
            values = ()
        elif isinstance(values, str):
            values = tuple(str_to_string(values))
        else:
            values = tuple(Symbol(x) for x in values)
        object.__setattr__(self, 'values', values)

    def __len__(self):
        return len(self.values)
    def __getitem__(self, i):
        if isinstance(i, slice):
            return String(self.values[i])
        else:
            return self.values[i]

    def __str__(self):
        if len(self.values) == 0:
            return 'ε'
        else:
            return ' '.join(map(str, self.values))
    def _repr_html_(self):
        if len(self.values) == 0:
            return 'ε'
        else:
            return ' '.join(map(repr_html, self.values))

    def __add__(self, other):
        return String(self.values + other.values)
    def __mul__(self, n):
        return String(self.values * n)
    def __rmul__(self, n):
        return String(n * self.values )

class Tuple(tuple):
    def __str__(self):
        return '('+','.join(map(str, self))+')'
    def _repr_html_(self):
        return '(' + ','.join(map(repr_html, self)) + ')'

class Set(frozenset):
    def __str__(self):
        if len(self) == 0:
            return '∅'
        else:
            return '{' + ",".join(map(str, sorted(self))) + '}'
    def _repr_html_(self):
        if len(self) == 0:
            return '∅'
        else:
            return '{' + ",".join(map(repr_html, sorted(self))) + '}'
