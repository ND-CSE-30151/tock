import unittest
import tock
from tock.regexps import *
from tock.regexps import symbol, union, concatenation, star

class TestRegexpParser(unittest.TestCase):
    def setUp(self):
        a, b, c, d = symbol('a'), symbol('b'), symbol('c'), symbol('d')
        self.cases = [
                (
                    '(c ∪ a) (b c ∪ d)*',
                    concatenation([
                        union([c, a]),
                        star(union([concatenation([b, c]), d]))
                    ])
                ),
            
            (
                'ε',
                concatenation([])
            )
        ]
        
    def test_parser(self):
        for s, r in self.cases:
            self.assertEqual(RegularExpression.from_str(s), r)
            
    def test_printer(self):
        for s, r in self.cases:
            self.assertEqual(str(r), s)

    def test_unicode(self):
        self.assertEqual(RegularExpression.from_str('&'), RegularExpression.from_str('ε'))
        self.assertEqual(RegularExpression.from_str('a|b'), RegularExpression.from_str('a∪b'))

if __name__ == '__main__':
    unittest.main()



