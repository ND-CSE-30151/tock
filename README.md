Tock
====

Tock stands for Theory Of Computing toolKit. It can simulate the
automata taught in standard theory of computation courses
(deterministic and nondeterministic finite automata, pushdown
automata, and Turing machines). It also allows multiple cells, stacks,
or tapes.

The documentation is contained in a series of [IPython] notebooks:

- [Introduction](Introduction.ipynb)
- [Deterministic finite automata](DFAs.ipynb)
- [Nondeterministic finite automata](NFAs.ipynb)
- [Regular expressions](Regexps.ipynb)
- [Pushdown automata](PDAs.ipynb)
- [Context free grammars](CFGs.ipynb)
- [Turing machines](TMs.ipynb)

Installation
------------

In order to view these notebooks, you'll need [IPython] and
[GraphViz]. The easiest way to get them is:

1. Install [Miniconda]. Either Python 2.7 or 3.x is fine.
2. Run `conda install six`.
3. Install [IPython] by running `conda install jupyter`.
4. If you don't have [GraphViz] already, don't worry; Tock downloads
   and uses [Viz.js] instead.

Then, run `ipython notebook` in the Tock directory. A web browser
should open, showing you the contents of the directory. Click on one
of the `.ipynb` files to view it.

[Miniconda]: http://conda.pydata.org/miniconda.html
[IPython]: http://ipython.org
[Graphviz]: http://www.graphviz.org
[Viz.js]: http://github.com/mdaines/viz.js/

Copying
-------

This is open-source software under the MIT License. See `LICENSE.md`
for more information.

