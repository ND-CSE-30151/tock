import unittest
import pathlib
from tock import *
from tock.machines import Transition, AlignedTransition

examples = pathlib.Path(__file__).parent.parent.joinpath('examples')

class TestRead(unittest.TestCase):
    def test_read_fa(self):
        m = read_csv(examples.joinpath('sipser-1-4.csv'))
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

    def test_read_pda(self):
        m = read_csv(examples.joinpath('sipser-2-14.csv'))
        self.assertEqual(set(m.states), {'q1', 'q2', 'q3', 'q4'})
        self.assertEqual(m.get_start_state(), 'q1')
        self.assertEqual(set(m.get_accept_states()), {'q4'})
        self.assertEqual(set(m.get_transitions()),
                         {AlignedTransition(['q1 → q2','&','& → $']),
                          AlignedTransition(['q2 → q2','0','& → 0']),
                          AlignedTransition(['q2 → q3','1','0 → &']),
                          AlignedTransition(['q3 → q3','1','0 → &']),
                          AlignedTransition(['q3 → q4','&','$ → &'])})
        
    def test_read_tm(self):
        m = read_csv(examples.joinpath('sipser-3-7.csv'))
        self.assertEqual(set(m.states), {'q1', 'q2', 'q3', 'q4', 'q5', 'qaccept', 'qreject'})
        self.assertEqual(m.get_start_state(), 'q1')
        self.assertEqual(set(m.get_accept_states()), {'qaccept'})
        
    def test_to_table(self):
        m = FiniteAutomaton()
        m.set_start_state('q1')
        m.add_accept_state('q2')
        m.add_transition('q1, a -> q2')
        t = to_table(m)
        self.assertEqual(t.rows, [['', 'a'], ['>q1', 'q2'], ['@q2', '']])
