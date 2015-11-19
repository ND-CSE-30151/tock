import collections
import six
from . import syntax

try:
    import IPython.display
    from . import viz
except ImportError:
    pass

__all__ = ['display_table']

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
    states.update(final_states)

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

