import unittest
import pathlib
from tock import *
from tock.machines import Transition, AlignedTransition

examples = pathlib.Path(__file__).parent.parent.joinpath('examples')

class TestRead(unittest.TestCase):
    def test_read_tgf(self):
        m = read_tgf(examples.joinpath('sipser-1-4.tgf'))
        self.assertEqual(set(m.states), {'q1', 'q2', 'q3'})
        self.assertEqual(m.get_start_state(), 'q1')
        self.assertEqual(set(m.get_accept_states()), {'q2'})
        self.assertEqual(set(m.get_transitions()),
                         {AlignedTransition(['q1 → q1','0']),
                          AlignedTransition(['q1 → q2','1']),
                          AlignedTransition(['q2 → q3','0']),
                          AlignedTransition(['q2 → q2','1']),
                          AlignedTransition(['q3 → q2','0']),
                          AlignedTransition(['q3 → q2','1'])})

    def test_to_graph(self):
        m = FiniteAutomaton()
        m.set_start_state('q1')
        m.add_accept_state('q2')
        m.add_transition('q1, a -> q2')
        g = to_graph(m)
        self.assertEqual(g.nodes, {'q1': {'start': True}, 'q2': {'accept': True}})
        self.assertEqual(g.edges, {'q1': {'q2': [{'label': AlignedTransition(['a'])}]}})
