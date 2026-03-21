Machines
========

Module tock.machines
--------------------

.. automodule:: tock.machines

   .. autoclass:: Machine

      **High-level interface**

      .. attribute:: store_types

         A list of store types, one for each store.
      .. autoproperty:: num_stores

      .. automethod:: add_transition
      .. automethod:: add_transitions
      .. automethod:: get_transitions
      .. autoproperty:: states
                        
      .. automethod:: set_start_state
      .. automethod:: get_start_state
      .. automethod:: add_accept_state
      .. automethod:: add_accept_states
      .. automethod:: get_accept_states
                      
      **Low-level interface**

      .. attribute:: transitions

         List of transitions.
      .. attribute:: start_config

         The start configuration.
      .. attribute:: accept_configs

         Set of accept configurations.
      
      **Tests for different types of automata**

      .. automethod:: is_finite
      .. automethod:: is_pushdown
      .. automethod:: is_turing
      .. automethod:: is_deterministic

   .. autoclass:: Store

      .. attribute:: values

         A sequence of Symbols
         
      .. attribute:: position

         The head position, between -1 and ``len(values)``.

      .. automethod:: match
                      
   .. autoclass:: Configuration

      .. attribute:: stores

         A tuple of Stores.

      .. automethod:: match
                      
   .. autoclass:: Transition

      .. attribute:: lhs

         Left-hand side Configuration.
      .. attribute:: rhs

         Right-hand side Configuration.

      .. automethod:: match
      .. automethod:: apply

   .. autoclass:: AlignedTransition
                      
Module tock.operations
----------------------

.. automodule:: tock.operations
   :members:

Module tock.run
---------------

.. automodule:: tock.run
   :members:
