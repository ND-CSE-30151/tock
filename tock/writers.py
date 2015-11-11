import collections
import six
from . import syntax

try:
    import IPython.display
    from . import viz
except ImportError:
    pass

__all__ = ['display_graph', 'display_table']

def display_graph(m):
    dot = six.StringIO()
    write_dot(m, dot)
    return viz.viz(dot.getvalue())

def display_table(m):
    out = six.StringIO()
    write_html(m, out)
    return IPython.display.HTML(out.getvalue())

def configs_to_string(configs):
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
            strings.append('(%s)' % ','.join(map(str, config)))
    return '{%s}' % ','.join(strings)

def ascii_to_html(s):
    s = str(s)
    s = s.replace("&", "&epsilon;")
    s = s.replace("->", "&rarr;")
    s = s.replace(">", "&gt;")
    return s

def write_html(m, file):
    """Writes an automaton's transition matrix as an HTML table."""
    file.write('<table style="font-family: Courier, monospace;">\n')
    states = set()
    initial_state = m.start_config[0][0]
    final_states = [config[0][0] for config in m.accept_configs if list(config[m.input]) == [syntax.BLANK]]
    conditions = set()
    transitions = collections.defaultdict(list)

    for t in m.get_transitions():
        lhs, rhs = t.lhs, t.rhs
        if len(lhs[0]) != 1: 
            raise ValueError("can't convert to table")
        q = lhs[0][0]
        r = rhs[0][0]
        condition = lhs[1:]

        states.add(q)
        conditions.add(condition)
        transitions[q,condition].append(rhs)

    conditions = sorted(conditions)

    file.write("  <tr><td></td>")
    for condition in conditions:
        file.write("<th>%s</th>" % ','.join(map(ascii_to_html, condition)))
    file.write("</tr>\n")
    for q in sorted(states):
        qstring = q
        if q == initial_state:
            qstring = ">" + qstring
        if q in final_states:
            qstring = "@" + qstring
        file.write("  <tr><th>%s</th>" % ascii_to_html(qstring))
        for condition in conditions:
            file.write('<td>%s</td>' % ascii_to_html(configs_to_string(transitions[q,condition])))
        file.write("</tr>\n")
    file.write("</table>\n")

def write_dot(m, file):
    """Writes an automaton's transition function in GraphViz dot format."""
    file.write("digraph {\n")
    file.write('  rankdir=LR;\n')
    file.write('  node [fontname=Courier,fontsize=10,shape=box,style=rounded,height=0,width=0,margin="0.055,0.042"];\n')
    file.write("  edge [arrowhead=vee,arrowsize=0.5,fontname=Courier,fontsize=9];\n")
    states = set()
    transitions = collections.defaultdict(list)
    initial_state = m.start_config[0][0]
    final_states = [config[0][0] for config in m.accept_configs if list(config[m.input]) == [syntax.BLANK]]

    for t in m.get_transitions():
        lhs, rhs = t.lhs, t.rhs
        q = lhs[0][0]
        r = rhs[0][0]
        states.add(q)
        states.add(r)
        transitions[q,r].append((lhs[1:], rhs[1:]))

    states = sorted(states)
    id_to_state = {}
    file.write('  START[shape=none,label=""];\n')
    for i, q in enumerate(states):
        if q in final_states:
            file.write('  %s[label="%s",peripheries=2];\n' % (i, q,))
        else:
            file.write('  %s[label="%s"];\n' % (i, q,))
        if q == initial_state:
            file.write('  START -> %s;\n' % i)
        id_to_state[q] = i
    for (q,r), ts in transitions.items():
        labels = []
        for (lhs, rhs) in sorted(ts):
            label = ','.join(map(str, lhs))
            if len(rhs) > 0:
                label = label + " -> " + ", ".join(map(str, rhs))
            labels.append("<tr><td>%s</td></tr>" % ascii_to_html(label))
        file.write('  %s -> %s[label=<<table border="0" cellpadding="1">%s</table>>];\n' % (id_to_state[q], id_to_state[r], ''.join(labels)))
    file.write("}\n")
