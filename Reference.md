Internal representation
=======================

Internally, all kinds of automata are represented in the same way. They have one or more _stores_, which are, in the most general case, half-infinite tapes, but you can use them as a finite state or as a stack.

The operation of the automaton is defined by transitions of the form
```
			    a,b,c -> x,y,z
```
where the left-hand side and right-hand side must have the same number of elements as there are stores. The meaning of the rule is that if the current symbol on the first store is `a`, replace it with `x`.

You don't actually write transitions in the above form; instead, write them as tables or graphs, as described below.

Transitions
===========

The left-hand sides and right-hand sides of transitions are tuples of one of the following:

- Empty (`&`), in which case the head is understood to be immediately to the _right_;
- A single symbol, which is the symbol under the head;
- Any number of (space-separated) symbols with a single `^` character somewhere, which indicates the head position. The symbol under the head is unspecified. There's no deep reason for this; it's just a limitation of the notation. (In the future, we may also allow `[a]` to represent both the head position and the symbol under the head.)

Despite the peculiarities of this notation, it can describe all the possible moves that typical automata make:

- `a -> b`: write symbol and don't move
- `a -> b^`: write symbol and move right
- `a -> ^b`: write symbol and move left
- `& -> b`: push symbol on left
- `a -> &`: pop symbol on left

States and symbols
==================

The first store is always the state. The start state is always called `START`, and the accept state and reject states are always called `ACCEPT` and `REJECT`, respectively.

The second store is always the input. It is initialized with the input string, followed by an infinite number of blank symbols (`_`). In FAs and PDAs you should not use `_` as an alphabet symbol.

There are some restrictions on states and symbols:
- The empty string (`&`) can't be used as a state or symbol.
- States and symbols should not contain the following special characters:
```
			     { } ( ) , ^
```
- States should not start with `>` or `@`.

Tables
======

Tables are in CSV format.

The first column lists all the states, one per row. Precede the name of the start state with `>`, and precede the name of final states with `@`. These symbols are not part of the state name.

Each interior cell contains a set of transitions. The left-hand side is formed from the row header (the state) and the column header; the cell contains the right-hand side or a set of right-hand sides.

Graphs
======

Graphs are in Trivial Graph Format (`.tgf`).

The nodes are labeled with states, including the `>` and `@` flags as described above.

The edges are labeled with transitions, minus the state on both the left-hand side and right-hand side.

Unicode special characters
==========================

If you want your automata to look even more like the book, you can use the following Unicode characters.

Warning: Unicode has many characters that look alike. These are the only ones supported.

Purpose       | ASCII | Unicode | Code point
--------------|-------|---------|----------------
final state   | @     | ◎       | U+25CE Bullseye
initial state | >     | →       | U+2191 Rightwards arrow
empty set     | {}    | ∅       | U+2205 Empty set
empty string  | &     | ε       | U+03B5 Greek small letter epsilon
              |       | ϵ       | U+03F5 Greek lunate epsilon symbol
transition    | ->    | →       | U+2191 Rightwards arrow
blank         | _     | ␣       | U+2423 Open box
head position | ^     | ↴       | U+21B4 Rightwards arrow with corner downwards
