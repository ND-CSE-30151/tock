import collections
import csv
from . import machines
from . import syntax

__all__ = ['Table', 'from_table', 'read_csv', 'read_excel', 'to_table', 'write_csv']

class Table:
    """A simple class that just stores a list of lists of strings.

    Arguments:
        rows: list of lists of strings
        num_header_rows (int): number of header rows
        num_header_cols (int): number of header columns
    """
    def __init__(self, rows, num_header_cols=1, num_header_rows=1):
        self.rows = rows                       #: The table contents
        self.num_header_cols = num_header_cols #: Number of header rows
        self.num_header_rows = num_header_rows #: Number of header columns
    def __getitem__(self, i):
        return self.rows[i]
    def __len__(self):
        return len(self.rows)

    def _repr_html_(self):
        result = []
        result.append('<table style="font-family: monospace;">')

        for i, row in enumerate(self.rows):
            result.append('  <tr>')
            for j, cell in enumerate(row):
                cell = cell.replace('&', '&epsilon;')
                cell = cell.replace('>', '&gt;')
                if i < self.num_header_rows or j < self.num_header_cols:
                    result.append(f'    <th style="text-align: left">{cell}</th>')
                else:
                    result.append(f'    <td style="text-align: left">{cell}</td>')
            result.append('  </tr>')
        
        result.append('</table>')
        return '\n'.join(result)

def addr(i, j):
    return chr(ord('A')+j) + str(i+1)

def from_table(table):
    """Convert a `Table` to a `Machine`.

    Example:

        +------+------+------+------+------+------+------+
        |      | 0    |      | 1    |      | &    |      |
        +------+------+------+------+------+------+------+
        |      | 0    | &    | 1    | &    | $    | &    |
        +======+======+======+======+======+======+======+
        | >@q1 |      |      |      |      |      | q2,$ |
        +------+------+------+------+------+------+------+
        |   q2 |      | q2,0 |      | q2,1 |      | q3,& |
        +------+------+------+------+------+------+------+
        |   q3 | q3,& |      | q3,& |      | q4,& |      |
        +------+------+------+------+------+------+------+
        |  @q4 |      |      |      |      |      |      |
        +------+------+------+------+------+------+------+

    The first two rows, because they have empty first cells, are
    assumed to be header rows.

    In a header row, cells "fill" to the right. In the above example,
    the first row effectively has cells 0, 0, 1, 1, &, &.
    """

    start_state = None
    accept_states = set()
    transitions = []

    header = True
    lhs2 = []
    for i, row in enumerate(table):
        # Skip totally blank rows
        if all(cell.strip() == '' for cell in row):
            continue
        
        # Header rows are rows whose first cell is empty
        if header and row[0].strip() != '':
            header = False

        if header:
            # Header rows have lhs values for all stores other than the first
            c = None
            for j, cell in enumerate(row[1:], 1):
                try:
                    if cell.strip() == '':
                        # Empty headings copy from the previous heading
                        if c is None:
                            raise ValueError('missing header')
                    else:
                        c = tuple(syntax.str_to_config(cell))
                except Exception as e:
                    e.message = f"cell {addr(i,j)}: {e.message}"
                    raise
                while j-1 >= len(lhs2):
                    lhs2.append(())
                lhs2[j-1] += c
        else:
            # First cell has lhs value for the first store
            try:
                q, attrs = syntax.str_to_state(row[0])
                if attrs.get('start', False):
                    if start_state is not None:
                        raise ValueError("more than one start state")
                    start_state = q
                if attrs.get('accept', False):
                    accept_states.add(q)
                lhs1 = ([q],)
            except Exception as e:
                e.message = f"cell {addr(i,0)}: {e.message}"
                raise

            # Rest of row has right-hand sides
            if len(row[1:]) != len(lhs2):
                raise ValueError(f"row {i+1}: row has wrong number of cells")
            for j, cell in enumerate(row[1:], 1):
                try:
                    for rhs in syntax.str_to_configs(cell):
                        transitions.append((lhs1+lhs2[j-1], rhs))
                except Exception as e:
                    e.message = f"cell {addr(i,j)}: {e.message}"
                    raise
        
    if start_state is None:
        raise ValueError("missing start state")
                
    return machines.from_transitions(transitions, start_state, accept_states)

def read_csv(filename):
    """Reads a CSV file containing a tabular description of a transition
       function (see `from_table`).
    """

    with open(filename) as file:
        table = list(csv.reader(file))
    m = from_table(table)
    return m

def read_excel(filename, sheet=None):
    """Reads an Excel file containing a tabular description of a
       transition function (see `from_table`).
    """

    from openpyxl import load_workbook # type: ignore
    wb = load_workbook(filename)
    if sheet is None:
        ws = wb.active
    else:
        ws = wb.get_sheet_by_name(sheet)
    table = [[cell.value or "" for cell in row] for row in ws.rows]
    return from_table(table)

def to_table(m):
    """Converts a `Machine` to a `Table`."""
    rows = []

    states = set()
    initial_state = m.get_start_state()
    final_states = m.get_accept_states()
    conditions = set()
    transitions = collections.defaultdict(list)

    for t in m.get_transitions():
        state = t[m.state]
        [[q]] = state.lhs
        [[r]] = state.rhs
        
        t = t[:m.state] + t[m.state+1:]
        lhs = tuple(t.lhs)
        rhs = (r,)+tuple(t.rhs)
        
        states.add(q)
        conditions.add(lhs)
        transitions[q,lhs].append(rhs)
    states.update(final_states)

    conditions = sorted(conditions)
    num_header_rows = len(conditions[0])
    for j in range(num_header_rows):
        row = ['']
        prev = None
        for condition in conditions:
            row.append(str(condition[j]) if condition[j] != prev else '')
            prev = condition[j]
        rows.append(row)

    for q in sorted(states):
        row = []
        qstring = q
        if q in final_states:
            qstring = "@" + qstring
        if q == initial_state:
            qstring = ">" + qstring
        row.append(qstring)
        for condition in conditions:
            row.append(syntax.configs_to_str(transitions[q,condition]))
        rows.append(row)
    return Table(rows, num_header_rows=num_header_rows)

def write_csv(m, filename):
    """Writes `Machine` `m` to file named by `filename`."""
    t = to_table(m)
    with open(filename, 'w') as file:
        writer = csv.writer(file)
        for i, row in enumerate(t.rows):
            if i < t.num_header_rows:
                assert row[0] == ''
            writer.writerow(row)
