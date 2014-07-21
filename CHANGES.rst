Changes in the development version
==================================

Nothing so far.

Changes in version 0.2.0
========================

Backwards-incompatible changes
------------------------------

* The non-standard parameter ``networks`` in the ``create_node`` driver
  method has been renamed to ``ex_networks``, in order to signal that
  it's non-standard.

Backwards-compatible changes
----------------------------

* New driver method ``ex_list_networks()`` which returns a list of
  defined networks.

Bug fixes
---------

* The driver method ``deploy_node()`` was badly broken:

  * It did not work if the node had not been created before.
  * It did not return the node object for the created node.


Changes in version 0.1.0
========================
Initial release.
