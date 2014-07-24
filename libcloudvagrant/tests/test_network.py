# Copyright (c) 2014 Carlos Valiente
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Unit tests for network code."""

import logging
import subprocess

import netifaces

from libcloud.common.types import LibcloudError

from libcloudvagrant.tests import new_driver, sample_network, sample_node


__all__ = [
    "test_create_network",
    "test_create_duplicate_netwoks",
    "test_destroy_network",
    "test_exhausted_networks",
    "test_host_interface_cleanup",
    "test_list_networks",
    "test_overlapping_networks",
    "test_public_network",
    "test_public_and_private_networks",
]


driver = new_driver()


def test_create_network():
    """Network objects are opaque. For unit tests, some operations are
    supported.

    """
    with sample_network("net1", cidr="192.168.0.0/24") as n:
        assert len(n.addresses) == 254
        for addr in n.addresses:
            assert addr in n


def test_create_duplicate_netwoks():
    """Networks with the same name may be created, as long as they are equal
    to those already created.

    """
    with sample_network("net1", cidr="192.168.0.0/24") as net1:
        net2 = driver.ex_create_network(name="net1", cidr="192.168.0.0/24")
        assert net1 == net2

    with sample_network("net1", cidr="192.168.0.0/24") as net1:
        try:
            driver.ex_create_network(name="net1", cidr="10.0.0.0/8")
        except Exception, exc:
            assert exc.value == "Network 'net1' already defined"
        else:
            raise AssertionError("Non-equal duplicate networks "
                                 "cannot be created")


def test_destroy_network():
    """Networks in use may not be destroyed.

    """
    with sample_network("net1") as net1:
        with sample_node(networks=[net1]):
            assert not driver.ex_destroy_network(net1)

        assert driver.ex_destroy_network(net1)


def test_exhausted_networks():
    """Networks cannot be over-allocated.

    """
    with sample_network("net1", cidr="172.16.0.0/30", public=True) as net:
        addr = net.allocate_address()
        assert str(addr.address) == "172.16.0.2"

        try:
            addr = net.allocate_address()
        except LibcloudError, exc:
            assert exc.value == "No more free addresses in 172.16.0.0/30"
        else:
            raise AssertionError("Address %s should not be available" %
                                 (addr,))


def test_host_interface_cleanup():
    """Host interfaces are removed when their associated networks are
    destroyed.

    """
    assert not any(i.startswith("vboxnet") for i in netifaces.interfaces())

    with sample_network("pub", public=True) as pub:
        with sample_node(networks=[pub]):
            iface = pub.host_interface
            assert iface in netifaces.interfaces()
        assert iface in netifaces.interfaces()
    assert iface not in netifaces.interfaces()

    with sample_network("priv") as priv:
        with sample_node(networks=[priv]):
            assert priv.host_interface is None


def test_list_networks():
    """Networks are listed properly.

    """
    assert len(driver.ex_list_networks()) == 0
    with sample_network("net1") as net1:
        networks = driver.ex_list_networks()
        assert len(networks) == 1
        assert networks[0] == net1

        with sample_network("net2") as net2:
            networks = driver.ex_list_networks()
            assert len(networks) == 2
            assert net1 in networks
            assert net2 in networks

        networks = driver.ex_list_networks()
        assert len(networks) == 1
        assert networks[0] == net1

    assert len(driver.ex_list_networks()) == 0


def test_overlapping_networks():
    """Overlapping networks are not supported.

    """
    with sample_network("net1", cidr="192.168.0.0/24"):
        try:
            driver.ex_create_network(name="net2",
                                     cidr="192.168.0.0/23")
        except Exception, exc:
            assert exc.value == "Network 'net2' overlaps with 'net1'"
        else:
            raise AssertionError("Overlapping networks are not supported")

        try:
            driver.ex_create_network(name="net2",
                                     cidr="192.168.0.0/25")
        except Exception, exc:
            assert exc.value == "Network 'net2' overlaps with 'net1'"
        else:
            raise AssertionError("Overlapping networks are not supported")


def test_public_network():
    with sample_network("public", public=True) as pub:
        with sample_node(networks=[pub]) as n:
            assert len(n.public_ips) == 1
            addr = n.public_ips[0]
            assert addr != pub.host_address
            assert ping(addr)
            assert not n.private_ips


def test_public_and_private_networks():
    """Public networks are accessible (within the host), but private ones are
    not.

    """
    pub = sample_network("public", public=True)
    dmz = sample_network("dmz")
    lan = sample_network("lan")

    with pub as pub, dmz as dmz, lan as lan:

        nginx = sample_node(networks=[pub, dmz])
        django = sample_node(networks=[dmz, lan])
        postgresql = sample_node(networks=[lan])

        with nginx as nginx, django as django, postgresql as postgresql:
            assert len(nginx.public_ips) == 1
            addr = nginx.public_ips[0]
            assert addr != pub.host_address
            assert ping(addr)

            assert len(nginx.private_ips) == 1
            addr = nginx.private_ips[0]
            assert not ping(addr)

            assert len(django.public_ips) == 0
            assert len(django.private_ips) == 2
            for addr in django.private_ips:
                assert not ping(addr)

            assert len(postgresql.public_ips) == 0
            assert len(postgresql.private_ips) == 1
            addr = postgresql.private_ips[0]
            assert not ping(addr)


LOG = logging.getLogger("libcloudvagrant")


def ping(addr):
    p = subprocess.Popen("ping -n -w 10 %s" % (addr,),
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    stdout, _ = p.communicate()
    LOG.debug("ping %s: %s", addr, stdout)
    if p.returncode == 0:
        return True
