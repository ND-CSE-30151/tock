import collections
import six
from . import syntax

try:
    import IPython.display
    from . import viz
except ImportError:
    pass

__all__ = ['to_table']

class Table(object):
    """A simple class that just stores a list of lists of strings.
    Compared to Graph, this is a lower-level representation."""
    def __init__(self, rows):
        self.rows = rows
    def __getitem__(self, i):
        return self.rows[i]
    def __len__(self):
        return len(self.rows)

    def _repr_html_(self):
        result = []
        result.append('<table style="font-family: Courier, monospace;">')

        for i, row in enumerate(self.rows):
            result.append('  <tr>')
            for j, cell in enumerate(row):
                cell = cell.replace('&', '&epsilon;')
                cell = cell.replace('>', '&gt;')
                if i == 0 or j == 0:
                    result.append('    <th>{}</th>'.format(cell))
                else:
                    result.append('    <td>{}</td>'.format(cell))
            result.append('  </tr>')
        
        result.append('</table>')
        return '\n'.join(result)

def to_table(m):
    rows = []

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
    row = ['']
    for condition in conditions:
        row.append(','.join(map(str, condition)))
    rows.append(row)

    for q in sorted(states):
        row = []
        qstring = q
        if q == initial_state:
            qstring = ">" + qstring
        if q in final_states:
            qstring = "@" + qstring
        row.append(qstring)
        for condition in conditions:
            row.append(configs_to_string(transitions[q,condition]))
        rows.append(row)
    return Table(rows)

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

