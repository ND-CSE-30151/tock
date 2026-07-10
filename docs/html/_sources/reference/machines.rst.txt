Machines
========

Module tock.machines
--------------------

.. automodule:: tock.machines

   .. autoclass:: Machine

      **High-level interface**

      .. attribute:: store_types

         A tuple of store types, one for each store.
      .. autoproperty:: num_stores
      .. autoproperty:: states

      .. automethod:: add_transition
      .. automethod:: add_transitions
      .. automethod:: get_transitions
                        
      .. automethod:: set_start_state
      .. automethod:: get_start_state
      .. automethod:: add_accept_state
      .. automethod:: add_accept_states
      .. automethod:: get_accept_states
                      
      **Low-level interface**

      .. attribute:: transitions

         A list of transitions.
      .. attribute:: start_config

         The start configuration.
      .. attribute:: accept_configs

         A set of accept configurations.
      
      **Tests for different types of automata**

      .. automethod:: is_finite
      .. automethod:: is_pushdown
      .. automethod:: is_turing
      .. automethod:: is_deterministic

   .. autoclass:: Store

      .. attribute:: values

         A sequence of symbols.
         
      .. attribute:: position

         The head position, between ``-1`` and ``len(values)``.

      .. automethod:: match
                      
   .. autoclass:: Configuration

      .. attribute:: stores

         A tuple of Stores.

      .. automethod:: match
                      
   .. autoclass:: Transition

      .. attribute:: lhs

         The left-hand-side configuration.
      .. attribute:: rhs

         The right-hand-side configuration.

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
