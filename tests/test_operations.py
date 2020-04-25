import unittest
import tock

class TestEquivalence(unittest.TestCase):
    def test_equivalence(self):
        m1 = tock.determinize(tock.from_regexp("((&|1|1 1) 0 0*)* (&|1|1 1)"))
        m2 = tock.determinize(tock.from_regexp("(0|1(0|1 0))*(&|1(1|&))"))

        self.assertTrue(tock.equivalent(m1, m2))

class TestIntersection(unittest.TestCase):
    def test_intersection(self):
        m1 = tock.FiniteAutomaton()
        m1.set_start_state('q1')
        m1.add_accept_state('q1')
        m1.add_transitions(['q1, a -> q2',
                            'q2, a -> q1'])
        m2 = tock.FiniteAutomaton()
        m2.set_start_state('q1')
        m2.add_accept_state('q1')
        m2.add_transitions(['q1, a -> q2',
                            'q2, a -> q3',
                            'q3, a -> q1'])
        m = tock.intersect(m1, m2)
        self.assertEqual(tock.run(m, ['a']*0).has_path(), True)
        self.assertEqual(tock.run(m, ['a']*1).has_path(), False)
        self.assertEqual(tock.run(m, ['a']*2).has_path(), False)
        self.assertEqual(tock.run(m, ['a']*3).has_path(), False)
        self.assertEqual(tock.run(m, ['a']*6).has_path(), True)

