libcloud-vagrant - A Vagrant compute provider for Apache Libcloud
=================================================================

``libcloud-vagrant`` is a compute provider for `Apache Libcloud`_ which uses
`Vagrant`_ to create `VirtualBox`_ nodes.

With ``libcloud-vagrant`` installed, you could prototype a small cluster on
your laptop, for instance, and then deploy it later on to Amazon, Rackspace,
or any of the other clouds supported by Libcloud.


Hello, world
------------

The following snippet spins up a virtual machine running on your host::

    from libcloud.compute.providers import get_driver

    from libcloudvagrant.driver import VAGRANT


    driver = get_driver(VAGRANT)()

    pub = driver.ex_create_network(name="pub", cidr="172.16.0.0/16", public=True)

    node = driver.create_node(name="n1",
                              image=driver.get_image("hashicorp/precise64"),
                              size=driver.list_sizes()[0],
                              networks=[pub])

    print "Node '%s' running!" % (node.name,)
    print ("Connect to it with 'ssh vagrant@%s' (password: 'vagrant')" %
           (node.public_ips[0],))


Features
--------

``libcloud-vagrant`` uses Vagrant to create boxes, networks and volumes. It
creates a Vagrant environment under ``~/.libcloudvagrant``, which is used
to run as many Vagrant boxes as you define.

Nodes created by ``libcloud-vagrant`` may be connected to *public networks*
or to *private networks*. Public networks are implemented as VirtualBox
`host-only`_ networks, and private networks are implemented as VirtualBox
`internal`_ networks.

``libcloud-vagrant`` also lets you create `VDI disks`_, and attach them to
the `SATA controllers`_ of your nodes.

Deployment scripts are run through Vagrant's NAT interface, using
Vagrant's SSH credentials. Therefore they also work for non-networked
nodes.


Requirements
------------

``libcloud-vagrant`` requires:

* `VirtualBox`_ (tested with version 4.3.12 under 64-bit Linux).
* `Vagrant`_ (tested with version 1.6.3 under 64-bit Linux).
* Python 2.7.


Installation
------------

Once you have installed VirtualBox and Vagrant, do the usual::

    $ pip install libcloud-vagrant

That will install ``libcloud-vagrant`` and its Python dependencies. You
might want to do that within a virtualenv.


More examples
-------------

Have a look at the `samples`_ subdirectory of the source distribution. You
wil find there a few scripts to create a single node, to show you how to
provision it, and a script which creates a two-node cluster.


.. _Apache Libcloud:   https://libcloud.apache.org/
.. _Vagrant:           http://vagrantup.com/
.. _VirtualBox:        http://virtualbox.org/
.. _SATA controllers:  http://virtualbox.org/manual/ch05.html#harddiskcontrollers
.. _VDI disks:         http://virtualbox.org/manual/ch05.html#vdidetails
.. _host-only:         http://virtualbox.org/manual/ch06.html#network_hostonly
.. _internal:          http://virtualbox.org/manual/ch06.html#network_internal
.. _samples:           https://github.com/carletes/libcloud-vagrant/tree/master/samples
