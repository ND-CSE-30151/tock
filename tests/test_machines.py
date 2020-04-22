import unittest
import tock
from tock.machines import *
from tock.machines import Store, Configuration, Transition, AlignedTransition

class TestStore(unittest.TestCase):
    def test_init(self):
        a, b = tock.syntax.Symbol('a'), tock.syntax.Symbol('b')
        self.assertEqual(Store(), Store([], 0))
        self.assertEqual(Store('^ &'), Store([], -1))
        self.assertEqual(Store('&'), Store([], 0))
        self.assertEqual(Store('& ^'), Store([], 0))
        self.assertEqual(Store('a b'), Store([a, b], 0))
        self.assertEqual(Store('^ a b'), Store([a, b], -1))
        #self.assertEqual(Store('[a] b'), Store([a, b], 0)) # not implemented
        #self.assertEqual(Store('a [b]'), Store([a, b], 1)) # not implemented
        self.assertEqual(Store('a b ^'), Store([a, b], 2))
        self.assertRaises(ValueError, lambda: Store('^ a b ^'))
        self.assertEqual(Store(['a', 'b']), Store([a, b], 0))
        self.assertEqual(Store(['a', 'b'], 1), Store([a, b], 1))
        s = Store('a b c', 1)
        self.assertEqual(s, Store(s))

    def test_hash(self):
        s = set()
        s.add(Store('a b', 0))
        s.add(Store('a b', 1))
        s.add(Store('a b c', 0))
        s.add(Store('a b', 1))
        self.assertEqual(len(s), 3)

    def test_sort(self):
        import itertools
        l = [Store('a b', 0), Store('a b', 1), Store('a b c', 0), Store('a b', 1)]
        l.sort()
        for lp in itertools.permutations(l):
            lp = list(lp)
            lp.sort()
            self.assertEqual(l, lp)

    def test_list(self):
        a, b, c = tock.syntax.Symbol('a'), tock.syntax.Symbol('b'), tock.syntax.Symbol('c')
        s = Store('a b c')
        self.assertEqual(list(s), [a, b, c])

    def test_str(self):
        a, b = tock.syntax.Symbol('a'), tock.syntax.Symbol('b')
        for s, ss in [
                (Store([], -1), '^ ε'),
                (Store([], 0), 'ε'),
                (Store([a], -1), '^ a'),
                (Store([a], 0), 'a'),
                (Store([a], 1), 'a ^'),
                (Store([a, b], -1), '^ a b'),
                (Store([a, b], 0), '[a] b'),
                (Store([a, b], 1), 'a [b]'),
                (Store([a, b], 2), 'a b ^'),
        ]:
            self.assertEqual(str(s), ss)

class TestConfiguration(unittest.TestCase):
    def test_init(self):
        abc, de = Store('a b c'), Store('d e')
        for c1, c2 in [
                (Configuration('a b c'), Configuration([abc])),
                (Configuration('&'), Configuration([[]])),
                (Configuration('a b c, d e'), Configuration([abc, de])),
                (Configuration(['a b c','d e']), Configuration([abc, de])),
                (Configuration([['a', 'b', 'c'], ['d', 'e']]), Configuration([abc, de])),
        ]:
            self.assertEqual(c1, c2)
        c = Configuration('a b c, d e')
        self.assertEqual(c, Configuration(c))

    def test_str(self):
        for c, sc in [
                (Configuration('a b c'), '[a] b c'),
                (Configuration('a b c, d e'), '[a] b c,[d] e'),
        ]:
            self.assertEqual(str(c), sc)

    def test_match(self):
        for pattern, config, result in [
                ([Store('a a', 1)], [Store('a a', 0)], False),
                ([Store('a a', 0)], [Store('a a', 0)], True),
                ([Store('a a', 0)], [Store('a b', 0)], False),
                ([Store('a a', 0)], [Store('a a', 1)], False),
                ([Store('a _', 0)], [Store('a a', 1)], True),
                ([Store('a _', 0)], [Store('a b', 1)], False),
                ('&', '&', True),
                ('&', 'a b', True),
        ]:
            pattern = Configuration(pattern)
            config = Configuration(config)
            self.assertEqual(pattern.match(config), result)
    
class TestTransition(unittest.TestCase):
    def test_init(self):
        abc, de = Store('a b c'), Store('d e')
        for t1, t2 in [
                (Transition('a b c -> d e'), Transition(Configuration([abc]), Configuration([de]))),
                (Transition('a b c, d e -> a b c, d e'), Transition(Configuration([abc, de]), Configuration([abc, de]))),
                (Transition('a b c'), Transition(Configuration([abc]), Configuration([]))),
                (Transition('a b c, d e'), Transition(Configuration([abc, de]), Configuration([]))),
        ]:
            self.assertEqual(t1, t2)

    def test_apply(self):
        for pattern, repl, config, result in [
                ([Store('a a', 1)], 'x y z', [Store('a a', 0)], None),
                ([Store('a a', 0)], 'x y z', [Store('a a', 0)], [Store('x y z')]),
                ([Store('a a', 0)], 'x y z', [Store('a b', 0)], None),
                ([Store('a a', 0)], 'x y z', [Store('a a', 1)], None),
                ([Store('a _', 0)], 'x y z', [Store('a a', 1)], [Store('a x y z', 1)]),
                ([Store('a _', 0)], 'x y z', [Store('a b', 1)], None),
                ('&', 'x y z', '&', 'x y z'),
                ('&', 'x y z', 'a b', 'x y z a b'),
                ([Store('a', 0)], [Store('b', 1)], [Store('a', 0)], [Store('b _', 1)]),
                ([Store('a', 0)], [Store('&', 0)], [Store('a', 0)], [Store('&', 0)]),
        ]:
            trans = Transition(Configuration(pattern), Configuration(repl))
            config = Configuration(config)
            if result is None:
                self.assertRaises(ValueError, lambda: trans.apply(config))
            else:
                result = Configuration(result)
                self.assertEqual(trans.apply(config), result)

class TestAlignedTransition(unittest.TestCase):
    def test_index(self):
        t = AlignedTransition(['a, b -> c', 'd -> e, f'])
        self.assertEqual(t[0], Transition('a, b -> c'))
        self.assertEqual(t[1], Transition('d -> e, f'))
        self.assertEqual(t[:], t)

    def test_add(self):
        t = AlignedTransition(['a, b -> c', 'd -> e, f'])
        self.assertEqual(t+t, AlignedTransition(['a, b -> c', 'd -> e, f', 'a, b -> c', 'd -> e, f']))

    def test_sides(self):
        t = AlignedTransition(['a, b -> c', 'd -> e, f'])
        self.assertEqual(t.lhs, Configuration('a, b, d'))
        self.assertEqual(t.rhs, Configuration('c, e, f'))
                
class TestMachine(unittest.TestCase):
    def test_fa(self):
        m = FiniteAutomaton()
        
        m.set_start_state('q1')
        self.assertEqual(m.get_start_state(), 'q1')
        m.set_start_state('q2')
        self.assertEqual(m.get_start_state(), 'q2')

        m.add_accept_state('q3')
        m.add_accept_state('q4')
        self.assertEqual(m.get_accept_states(), {'q3', 'q4'})

        m.add_transition(Transition('q2, a -> q3'))
        m.add_transition('q3, b -> q4')
        self.assertEqual(set(m.get_transitions()),
                         {AlignedTransition(['q2 -> q3', 'a']),
                          AlignedTransition(['q3 -> q4', 'b'])})
        
        self.assertTrue(m.is_finite())
        self.assertTrue(m.is_deterministic())
        self.assertFalse(m.is_pushdown())
        self.assertFalse(m.is_turing())
    
    def test_pda(self):
        m = PushdownAutomaton()
        
        m.set_start_state('q1')
        self.assertEqual(m.get_start_state(), 'q1')
        m.set_start_state('q2')
        self.assertEqual(m.get_start_state(), 'q2')

        m.add_accept_state('q3')
        m.add_accept_state('q4')
        self.assertEqual(m.get_accept_states(), {'q3', 'q4'})

        m.add_transition(Transition('q2, a, & -> q3, x'))
        m.add_transition('q3, b, x -> q4, y')
        self.assertEqual(set(m.get_transitions()),
                         {AlignedTransition(['q2 -> q3', 'a', '& -> x']),
                          AlignedTransition(['q3 -> q4', 'b', 'x -> y'])})
        
        self.assertFalse(m.is_finite())
        self.assertTrue(m.is_pushdown())
        self.assertTrue(m.is_deterministic())
        self.assertFalse(m.is_turing())
    
    def test_tm(self):
        m = TuringMachine()
        
        m.set_start_state('q1')
        self.assertEqual(m.get_start_state(), 'q1')
        m.set_start_state('q2')
        self.assertEqual(m.get_start_state(), 'q2')

        m.add_accept_state('q3')
        m.add_accept_state('q4')
        self.assertEqual(m.get_accept_states(), {'q3', 'q4'})

        m.add_transition(Transition('q2, a -> q2, b, R'))
        m.add_transition('q2, b -> q3, c, L')
        self.assertEqual(set(m.get_transitions()),
                         {AlignedTransition(['q2 -> q2', 'a -> b, R']),
                          AlignedTransition(['q2 -> q3', 'b -> c, L'])})
        
        self.assertFalse(m.is_finite())
        self.assertFalse(m.is_pushdown())
        self.assertTrue(m.is_turing())
        self.assertTrue(m.is_deterministic())
    
if __name__ == '__main__':
    unittest.main()
