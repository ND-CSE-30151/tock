Internal representation of machines
===================================

Stores
------

Internally, all kinds of automata are represented in the same
way. They have one or more *stores*, which are half-infinite tapes,
but you don't have to use them as tapes; you can use them instead as
finite states or as stacks.

Transitions
-----------

The operation of the automaton is defined by transitions of the form::

    a,b,c -> x,y,z

where the left-hand side and right-hand side must have the same number
of elements as there are stores, and each element is a symbol
annotated with a head position. The meaning of the transition is that
if the first store matches ``a`` (relative to the current head
position), replace it with ``x``; if the second store matches ``b``,
replace it with ``y``; and so on.

In more detail, each element is either empty (``&``) or a whitespace-separated
string of symbols, optionally preceded or followed by a caret (``^``).

- If the caret precedes the string, the head is one before the first symbol;
- If the caret follows the string, the head is one after the last symbol;
- If the caret is absent, the head is over the *first* symbol.

Note that ``^ &`` is different from ``& ^``, and ``&`` is the same as ``& ^``.

Despite the peculiarities of this notation, it can describe all the
possible moves that typical automata make:

- ``a -> b``: write symbol and don't move
- ``a -> b ^``: write symbol and move right
- ``a -> ^ b``: write symbol and move left
- ``& -> b``: push symbol on left
- ``a -> &``: pop symbol on left

States and symbols
------------------

States and symbols can be:

- A sequence of one or more letters, numbers, ``_``, or ``.``
- One of the following: ``|- -| # $``

Tables
------

Tables are in CSV format.

The first column lists all the states, one per row. Precede the name
of the start state with ``>``, and precede the name of final states with
``@``. These symbols are not part of the state name.

The first row lists all the possible left-hand sides of transitions,
sans state.

Each interior cell contains a set of right-hand sides.

Thus, the left-hand side is formed by concatenating the row header
(the state) and the column header; the right-hand side is taken from
the cell.

Graphs
------

Graphs are in Trivial Graph Format (TGF).

The nodes are labeled with states, including the ``>`` and ``@`` flags as
described above.

The edges are labeled with transitions, minus the state on both the
left-hand side and right-hand side.
