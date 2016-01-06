
Tock
====

Tock stands for Theory Of Computing toolKit. It can simulate the
automata taught in standard theory of computation courses (deterministic
and nondeterministic finite automata, pushdown automata, and Turing
machines). It also allows multiple cells, stacks, or tapes.

Installation
------------

Tock depends on the following:

-  Python 2.7 or 3.x (required)
-  `six <https://pypi.python.org/pypi/six>`__ (required)
-  `GraphViz <http://www.graphviz.org>`__ (to draw graphs)
-  `Jupyter <http://jupyter.org>`__/`IPython <http://ipython.org>`__ (to
   view notebooks)
-  `openpyxl <https://pypi.python.org/pypi/openpyxl>`__ (to open Excel
   files)

Steps:

1. Run ``pip install tock``.

2. Install
   `Jupyter <http://jupyter.org>`__/`IPython <http://ipython.org>`__ by
   running ``pip install jupyter`` (or ``conda install jupyter`` if you
   use Anaconda).

3. Install `GraphViz <http://www.graphviz.org>`__. But if you don't have
   it, Tock will attempt to download and use
   `Viz.js <https://github.com/mdaines/viz.js>`__, which is slower but
   otherwise identical.

Documentation
-------------

The documentation is contained in a series of
`IPython <http://ipython.org>`__ notebooks:

-  `Deterministic finite automata <doc/DFAs.ipynb>`__
-  `Nondeterministic finite automata <doc/NFAs.ipynb>`__
-  `Regular expressions <doc/Regexps.ipynb>`__
-  `Pushdown automata <doc/PDAs.ipynb>`__
-  `Context free grammars <doc/CFGs.ipynb>`__
-  `Turing machines <doc/TMs.ipynb>`__

To open them, run ``ipython notebook`` in the Tock directory. A web
browser should open, showing you the contents of the directory. Click on
``doc`` and then one of the ``.ipynb`` files to view it.

Copying
-------

This is open-source software under the MIT License. See ``LICENSE.txt``
for more information.
