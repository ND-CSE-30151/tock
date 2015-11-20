Tock
====

Tock stands for Theory Of Computing toolKit. It can simulate the
automata taught in standard theory of computation courses
(deterministic and nondeterministic finite automata, pushdown
automata, and Turing machines). It also allows multiple cells, stacks,
or tapes.

The documentation is contained in a series of [IPython] notebooks:

- [Deterministic finite automata](DFAs.ipynb)
- [Nondeterministic finite automata](NFAs.ipynb)
- [Regular expressions](Regexps.ipynb)
- [Pushdown automata](PDAs.ipynb)
- [Context free grammars](CFGs.ipynb)
- [Turing machines](TMs.ipynb)

Installation
------------

Tock depends on the following:

- Python 2.7 or 3.x (required)
- [six] (required)
- [GraphViz] (to draw graphs)
- [IPython] (to view notebooks)
- [openpyxl] (to open Excel files)

The easiest way to get started is:

1. Install [Miniconda]. Either Python 2.7 or 3.x is fine.
2. Run `conda install six jupyter openpyxl`.

If you don't have GraphViz, don't worry -- Tock will attempt to
download and use [Viz.js], which is slower but otherwise identical.

Then, run `ipython notebook` in the Tock directory. A web browser
should open, showing you the contents of the directory. Click on one
of the `.ipynb` files to view it.

[six]: https://pypi.python.org/pypi/six
[openpyxl]: https://pypi.python.org/pypi/openpyxl
[Miniconda]: http://conda.pydata.org/miniconda.html
[IPython]: http://ipython.org
[Graphviz]: http://www.graphviz.org
[Viz.js]: http://github.com/mdaines/viz.js

Copying
-------

This is open-source software under the MIT License. See `LICENSE.md`
for more information.

