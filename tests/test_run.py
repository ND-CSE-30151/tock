import unittest
from tock import *

class TestRun(unittest.TestCase):
    def test_fa(self):
        m = FiniteAutomaton()
        
        m.set_start_state('q1')
        m.add_accept_state('q3')
        m.add_transition('q1, a -> q2')
        m.add_transition('q2, b -> q3')

        path = run(m, 'a b').shortest_path()
        self.assertEqual(len(path), 3)

    def test_pda(self):
        m = PushdownAutomaton()
        
        m.set_start_state('q1')
        m.add_accept_state('q2')
        m.add_transition('q1, &, & -> q1, x')
        m.add_transition('q1, a, & -> q2, &')
        m.add_transition('q2, &, x -> q2, &')

        path = run(m, 'a').shortest_path()
        self.assertEqual(len(path), 2)
