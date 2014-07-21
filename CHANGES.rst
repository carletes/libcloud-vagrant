Changes in the development version
==================================

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
* The driver method ``deploy_node()`` did not return the node object.


Changes in version 0.1.0
========================
Initial release.
