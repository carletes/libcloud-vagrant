Changes in the development version
==================================

Backwards-compatible changes
----------------------------

* Volumes may be hot-plugged.

* Virtualbox shared folders are disabled, in order to make Vagrant boxes
  resemble more closely nodes created by other providers.

* Vagrant node instances have an extension attribute called ``ex_ssh_client``,
  a context manager wrapping an instance of ``libcloud.compute.ssh.SSHClient``.


Changes in version 0.3.0
========================

Backwards-incompatible changes
------------------------------

* Nodes have now an ``id`` field, matching the VirtualBox UUID.
  You must recreate all the nodes defined in your ``~/.libcloud-vagrant``
  catalogue.


Backwards-compatible changes
----------------------------

* New command-line tool ``libcloud-vagrant`` to do simple operations
  with Vagrant nodes created by Libcloud.

* Interactions with Vagrant and Virtualbox are protected by a
  filesystem-based lock.

* Unit tests use now a free 24-bit network in the 192.168/16 range,
  instead of using hard-coded ones.

* The host network interfaces of public networks are destroyed when the
  Vagrant network objects are destroyed.

* ``libcloud-vagrant`` now makes fewer calls to the Virtualbox
  ``VBoxManage`` command.


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
