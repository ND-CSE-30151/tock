# -*- coding: utf-8 -*-

import collections
import machines
import csv

# To do: better error reporting
# Abstract graph and table structures to read/write tgf, dot, csv, md

### Parser for transitions and pieces of transitions

class dotstring(str):
    def __init__(self, *args, **kwargs):
        str.__init__(self, *args, **kwargs)
        self.i = 0

    @property
    def c(self):
        return self[self.i]

def parse_whitespace(s):
    while s.i < len(s) and s.c.isspace():
        s.i += 1

# All the following methods are guaranteed to skip leading whitespace,
# and may or may not skip trailing whitespace.

def parse_character(s, c):
    n = len(c)
    parse_whitespace(s)
    if s.i+n > len(s):
        raise ValueError("expected %s, found end of string" % c)
    elif s[s.i:s.i+n] == c:
        s.i += n
    else:
        raise ValueError("expected %s, found %s" % (c, s.c))

def parse_end(s):
    parse_whitespace(s)
    if s.i < len(s):
        raise ValueError("unexpected %s" % (s.c))

def parse_symbol(s):
    parse_whitespace(s)
    i0 = s.i
    while s.i < len(s) and s.c not in ",)}^" and not s.c.isspace():
        s.i += 1
    return s[i0:s.i]

def parse_store(s):
    """Bugs: only handles single symbols."""
    position = None
    parse_whitespace(s)
    if s.c == '^':
        s.i += 1
        position = -1
    x = parse_symbol(s)
    if x == '&':
        x = []
    else:
        x = [x]
    parse_whitespace(s)
    if s.i < len(s) and s.c == '^':
        s.i += 1
        if position is not None:
            raise ValueError("head is only allowed to be in one position")
        position = len(x)
    if position is None:
        position = 0
    return machines.Store(x, position)

def parse_multiple(s, f, values=None):
    if values is None: values = []
    values.append(f(s))
    parse_whitespace(s)
    if s.i < len(s) and s.c == ',':
        s.i += 1
        return parse_multiple(s, f, values)
    else:
        return values

def parse_tuple(s):
    parse_character(s, '(')
    value = tuple(parse_multiple(s, parse_store))
    parse_character(s, ')')
    return value

def parse_set(s):
    parse_character(s, '{')
    parse_whitespace(s)
    if s.c == '(':
        value = set(parse_multiple(s, parse_tuple))
    else:
        value = {(x,) for x in parse_multiple(s, parse_store)}
    parse_character(s, '}')
    return value

def string_to_state(s):
    """s is a string possibly preceded by > or @."""
    s = dotstring(s)
    parse_whitespace(s)
    flags = set()
    while True:
        if s.c in '>@':
            flags.add(s.c)
            s.i += 1
            parse_whitespace(s)
        else:
            break
    x = parse_symbol(s)
    parse_end(s)
    return x, flags

def string_to_config(s):
    """s is a comma-separated list of stores."""
    s = dotstring(s)
    x = parse_multiple(s, parse_store)
    parse_end(s)
    return tuple(x)

def string_to_configs(s):
    """s is a string in one of the following formats:
       - x,y
       - (x,y)
       - {x,y}
       - {(w,x),(y,z)}
       In any case, returns a set of tuples of stores.
    """

    s = dotstring(s)
    value = None
    parse_whitespace(s)
    if s.i == len(s):
        value = set()
    elif s.c == '{':
        value = parse_set(s)
    elif s.c == '(':
        value = {parse_tuple(s)}
    else:
        value = {tuple(parse_multiple(s, parse_store))}
    parse_end(s)

    return value

def string_to_transition(s):
    """s is a string of the form a,b or a,b->c,d"""
    s = dotstring(s)
    lhs = parse_multiple(s, parse_store)
    parse_whitespace(s)
    if s.i+2 < len(s) and s[s.i:s.i+2] == "->":
        s.i += 2
        rhs = parse_multiple(s, parse_store)
    else:
        rhs = ()
    parse_end(s)
    return tuple(lhs), tuple(rhs)

### Utility functions

def ascii_to_html(s):
    return s.replace("&", "&epsilon;").replace("->", "&rarr;")

def single_value(s):
    s = set(s)
    if len(s) != 1:
        raise ValueError()
    return s.pop()

"""These functions act as an adapter between conventional machines and ours.

Conventional: initial state distinguished
Ours: initial state always ACCEPT

These conventions kick in when m.one_way_state() is True:

Conventional: final states distinguished; final state only active at end of input
Ours: final state always ACCEPT and is unconditional
Conventional: input symbol is always consumed (a -> &)
Ours: rewrite for input could be anything
"""

def add_initial_state(m, q, n):
    inputs = [machines.Store(['START'])] + [machines.Store()]*(n-1)
    outputs = [machines.Store([q])] + [machines.Store()]*(n-1)
    m.add_transition(machines.Transition(inputs, outputs))

def add_transition(m, l, r):
    # If necessary, supply implicit rhs for input,
    # which is always the *second* store
    if len(r) == len(l)-1:
        r = list(r)
        r[1:1] = [machines.Store()]
    m.add_transition(machines.Transition(l, r))

def add_final_state(m, q, n):
    inputs = [machines.Store([q]), machines.Store([machines.BLANK])] + [machines.Store()]*(n-2)
    outputs = [machines.Store(['ACCEPT'])] + [machines.Store()]*(n-1)
    m.add_transition(machines.Transition(inputs, outputs))

### Top-level functions for reading and writing machines in various formats.

def read_csv(infile):
    """Reads a CSV file containing a tabular description of a transition function,
       as found in Sipser. Major difference: instead of multiple header rows,
       only a single header row whose entries might be tuples.
       """
    if not isinstance(infile, file):
        infile = open(infile)

    reader = csv.reader(infile)
    lhs = []
    transitions = []

    # Header row has one dummy cell, and then each cell has lhs values
    # for the input and any additional stores.
    row = reader.next()
    lhs = []
    j = 1
    for cell in row[1:]: 
        try:
            lhs.append(string_to_config(cell))
        except Exception as e:
            raise ValueError("cell %s1: %s" % (chr(ord('A')+j), e.message))
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
            raise ValueError("cell A%d: %s" % (i+1, e.message))
        if '>' in flags:
            add_initial_state(m, q, n)
        if '@' in flags:
            add_final_state(m, q, n)

        rhs = []
        j = 1
        for cell in row[1:]:
            try:
                rhs.append(string_to_configs(cell))
            except Exception as e:
                raise ValueError("cell %s%d: %s" % (chr(ord('A')+j), i+1, e.message))
            j += 1
        for l, rs in zip(lhs, rhs):
            l = (machines.Store([q]),) + l
            for r in rs:
                add_transition(m, l, r)
        i += 1
    return m

def read_tgf(infile):
    """Reads a file in Trivial Graph Format."""
    if not isinstance(infile, file):
        infile = open(infile)

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
        add_transition(m, lhs, rhs)

    for i in states:
        if '>' in flags[i]:
            add_initial_state(m, states[i], m.num_stores)
        if '@' in flags[i]:
            add_final_state(m, states[i], m.num_stores)

    return m

def write_html(m, file):
    """Writes an automaton's transition matrix as an HTML table."""
    file.write('<table style="font-family: Courier, monospace;">')
    states = set()
    initial_state = None
    final_states = set()
    conditions = set()
    transitions = collections.defaultdict(list)
    one_way_input = m.one_way_input()
    for t in m.transitions:
        if len(t.inputs[0]) != 1: 
            raise ValueError("can't convert to table")
        q = t.inputs[0][0]
        r = t.outputs[0][0]
        condition = t.inputs[1:]

        if q == machines.START:
            # to do: also allow explicit START
            assert sum(len(i) for i in t.inputs[1:]) == 0
            assert sum(len(i) for i in t.outputs[1:]) == 0
            initial_state = r
        elif one_way_input and r == machines.ACCEPT and len(t.inputs[1]) == 1 and t.inputs[1][0] == machines.BLANK:
            final_states.add(q)
        else:
            states.add(q)
            if r not in [machines.ACCEPT, machines.REJECT]:
                states.add(r)
            conditions.add(condition)
            transitions[q,condition].append(t)

    file.write("  <tr><td></td>")
    for condition in conditions:
        file.write("<th>%s</th>" % ','.join(ascii_to_html(str(c)) for c in condition))
    for q in states:
        qstring = ascii_to_html(q)
        if q == initial_state:
            qstring = "&gt;" + qstring
        if q in final_states:
            qstring = "@" + qstring
        file.write("  <tr><th>%s</th>" % qstring)
        for condition in conditions:
            contents = []
            parens = False
            for t in transitions[q,condition]:
                outputs = [str(t.outputs[0])] + [ascii_to_html(str(r)) for r in t.outputs[1:]]
                if one_way_input:
                    outputs[1:2] = []
                if len(outputs) > 1:
                    parens = True
                contents.append(','.join(outputs))
            if len(contents) > 1 and parens:
                file.write('<td>{%s}</td>' % ('(%s)' % ','.join('%s' % tstring for tstring in contents)))
            elif len(contents) > 1:
                file.write('<td>{%s}</td>' % (','.join('%s' % tstring for tstring in contents)))
            elif len(contents) == 1:
                file.write("<td>%s</td>" % contents[0])
            else:
                file.write("<td></td>")
        file.write("  </tr>")
    file.write("</table>")

def write_dot(m, file):
    """Writes an automaton's transition function in GraphViz dot format."""
    file.write("digraph {\n")
    file.write('  rankdir=LR;\n')
    file.write('  node [fontname=Courier,fontsize=10,shape=box,style=rounded,height=0,width=0,margin="0.055,0.0277"];\n')
    file.write("  edge [arrowhead=vee,arrowsize=0.8,fontname=Courier,fontsize=9];\n")
    states = set()
    transitions = collections.defaultdict(list)
    initial_state = None
    final_states = set()

    for t in m.transitions:
        q = t.inputs[0][0]
        r = t.outputs[0][0]
        if q == machines.START:
            # to do: also allow explicit START
            assert sum(len(i) for i in t.inputs[1:]) == 0
            assert sum(len(i) for i in t.outputs[1:]) == 0
            initial_state = r
        elif m.one_way_input() and r == machines.ACCEPT and len(t.inputs[1]) == 1 and t.inputs[1][0] == machines.BLANK:
            final_states.add(q)
        else:
            states.add(q)
            states.add(r)
            transitions[q,r].append(t)

    states = list(states)
    id_to_state = {}
    for i, q in enumerate(states):
        if q in final_states:
            file.write('  %s[label="%s",peripheries=2];\n' % (i, q,))
        else:
            file.write('  %s[label="%s"];\n' % (i, q,))
        if q == initial_state:
            file.write('  START[shape=none,label=""];\n')
            file.write('  START -> %s;\n' % i)
        id_to_state[q] = i
    for (q,r), ts in transitions.iteritems():
        labels = []
        for t in ts:
            label = ','.join(map(str, t.inputs[1:]))
            if m.one_way_input():
                outputs = t.outputs[2:]
            else:
                outputs = t.outputs[1:]
            if len(outputs) > 0:
                label = label + " -> " + ", ".join(map(str, outputs))
            labels.append("<tr><td>%s</td></tr>" % ascii_to_html(label))
        file.write('  %s -> %s[label=<<table border="0" cellpadding="1">%s</table>>];\n' % (id_to_state[q], id_to_state[r], ''.join(labels)))
    file.write("}\n")

