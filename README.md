Tock
====

Tock stands for Theory Of Computing toolKit. It can simulate the
automata taught in standard theory of computation courses
(deterministic and nondeterministic finite automata, pushdown
automata, and Turing machines). It can also simulate many extensions,
like multiple stacks or tapes.

- [Project documentation](http://nd-cse-30151.github.io/tock/html/)

Installation
------------

Tock depends on the following:

-  Python 3.7 (required)
-  [Jupyter](http://jupyter.org) (to
   view notebooks)
-  [GraphViz](http://www.graphviz.org) (required system package; provides the `dot` executable used to draw and lay out graphs)
-  [pydot](https://pypi.org/project/pydot/) (required Python package; installed automatically by `pip install tock`)   
-  [anywidget](https://pypi.org/project/anywidget/) (required Python package for the interactive machine editor; installed automatically by `pip install tock`)  
-  [openpyxl](https://pypi.python.org/pypi/openpyxl) (to open Excel
   files)

Steps:

1. Run `pip install tock`.

2. If you want to run local Jupyter notebooks, install [Jupyter](http://jupyter.org) by running `pip install jupyter` (or `conda install jupyter` if you use Anaconda).

3. Install the system [GraphViz](http://www.graphviz.org) package so the `dot` executable is available on your `PATH`. This is separate from `pip install tock`: `pip` installs the Python packages (`pydot`, `anywidget`), but GraphViz itself must be installed through your operating system or environment.

Copying
-------

This is open-source software under the MIT License. See `LICENSE.txt`
for more information.
