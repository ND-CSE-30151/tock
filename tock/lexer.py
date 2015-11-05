import re

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

# Comments are introduced by //
comment_re = re.compile(r"\s*//.*")

# Symbols can be |- -| # $ or any string of alphanumerics or _ .
symbol_re = re.compile(r"\s*(\|-|-\||#|$|[A-Za-z0-9_.]+)")

# Operators
operator_re = re.compile(r"\s*(->|[&^(){},@>|*])")

def lexer(s):
    i = 0
    tokens = []
    while i < len(s):
        m = comment_re.match(s, i)
        if m:
            i = m.end(0)
            continue
        m = symbol_re.match(s, i) or operator_re.match(s, i)
        if not m:
            raise ValueError("couldn't understand input: %s" % s[i:])
        tokens.append(m.group(1))
        i = m.end(0)
    return Tokens(tokens)

