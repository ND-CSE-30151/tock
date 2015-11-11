import re

START = 'START'
ACCEPT = 'ACCEPT'
REJECT = 'REJECT'
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

whitespace_re = re.compile(r"\s*(//.*)?")

# Symbols can be |- -| # $ or any string of alphanumerics or _ .
symbol_re = re.compile(r"\|-|-\||#|\$|[A-Za-z0-9_.]+")
class Symbol(str):
    def __repr__(self):
        return "Symbol(%s)" % self

# Operators
operator_re = re.compile(r"->|[&^(){},@>|*]")
class Operator(str):
    def __repr__(self):
        return "Operator(%s)" % self

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

if __name__ == "__main__":
    import sys
    print(list(lexer(sys.argv[1])))
