tock: Theory of Computing toolKit
=================================

Tock stands for Theory Of Computing toolKit. It can simulate the
automata taught in standard theory of computation courses
(deterministic and nondeterministic finite automata, pushdown
automata, and Turing machines). It can also simulate many extensions,
like multiple stacks or tapes.

Installation
============

1. Install the Python package:

   .. code-block:: bash

      pip install tock

   This installs Tock's Python dependencies, including ``pydot``,
   ``anywidget``, and ``openpyxl``.

2. If you want to run local Jupyter notebooks, install Jupyter:

   .. code-block:: bash

      pip install jupyter

3. Install the system `GraphViz <https://graphviz.org/>`_ package so
   the ``dot`` executable is available on your ``PATH``.

   ``pip install tock`` installs the Python packages that talk to
   GraphViz, but GraphViz itself must be installed through your
   operating system or environment.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tutorial/index.rst
   reference/index.rst

Indexes
=======

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
