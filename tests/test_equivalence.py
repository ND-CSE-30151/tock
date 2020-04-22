import unittest
import tock

class TestEquivalence(unittest.TestCase):
    def test_equivalence(self):
        m1 = tock.determinize(tock.from_regexp("((&|1|1 1) 0 0*)* (&|1|1 1)"))
        m2 = tock.determinize(tock.from_regexp("(0|1(0|1 0))*(&|1(1|&))"))

        self.assertTrue(tock.equivalent(m1, m2))



