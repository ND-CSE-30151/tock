Machines
========

Module tock.machines
--------------------

.. automodule:: tock.machines
   :members: Path

   .. autoclass:: Machine

      **High-level interface**

      .. autoinstanceattribute:: store_types
         :annotation:
      .. autoproperty:: num_stores

      .. method:: add_transition(transition)
      .. automethod:: add_transition(lhs, rhs)
      .. automethod:: add_transitions
      .. automethod:: get_transitions
      .. autoproperty:: states
                        
      .. automethod:: set_start_state
      .. automethod:: get_start_state
      .. automethod:: add_accept_state
      .. automethod:: add_accept_states
      .. automethod:: get_accept_states
                      
      **Low-level interface**

      .. autoinstanceattribute:: transitions
         :annotation:
      .. autoinstanceattribute:: start_config
         :annotation:
      .. autoinstanceattribute:: accept_configs
         :annotation:
      
      **Tests for different types of automata**

      .. automethod:: is_finite
      .. automethod:: is_pushdown
      .. automethod:: is_turing
      .. automethod:: is_deterministic

   .. class:: Store(values=(), position=0)
   .. autoclass:: Store(store)

      .. attribute:: values

         A sequence of Symbols
         
      .. autoinstanceattribute:: position
         :annotation:

      .. automethod:: match
                      
   .. class:: Configuration(stores)
   .. autoclass:: Configuration(config)

      .. autoinstanceattribute:: stores
         :annotation:

      .. automethod:: match
                      
   .. class:: Transition(lhs, rhs)
   .. autoclass:: Transition(transition)

      .. autoinstanceattribute:: lhs
         :annotation:
      .. autoinstanceattribute:: rhs
         :annotation:

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
