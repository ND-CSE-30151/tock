import unittest
import tock
from tock.grammars import *
from tock.syntax import String

class TestGrammar(unittest.TestCase):
    def test_init(self):
        g = Grammar()
        g.set_start('S')
        g.add_nonterminal('T')
        g.add_rule('S', 'a S b')
        g.add_rule('S', 'T')
        g.add_rule('T', 'c T d')
        g.add_rule('T', '&')
        self.assertEqual(g.nonterminals, {'S', 'T'})
        self.assertEqual(set(g.rules), {(String('S'), String('a S b')),
                                        (String('S'), String('T')),
                                        (String('T'), String('c T d')),
                                        (String('T'), String('&'))})

        self.assertEqual(str(g), 'start: S\nS → a S b\nS → T\nT → c T d\nT → ε')

    def test_from_lines(self):
        g = Grammar.from_lines([
            'S -> a S b',
            'S -> &'
        ])
        self.assertEqual(g.nonterminals, {'S'})
        self.assertEqual(set(g.rules), {(String('S'), String('a S b')),
                                        (String('S'), String('&'))})

        self.assertEqual(str(g), 'start: S\nS → a S b\nS → ε')
