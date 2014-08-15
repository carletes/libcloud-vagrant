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

from pytest import raises

from libcloud.common.types import LibcloudError

from libcloudvagrant.tests import available_network, sample_network, sample_node


__all__ = [
    "test_create_network",
    "test_create_duplicate_netwoks",
    "test_destroy_network",
    "test_exhausted_networks",
    "test_host_interface_cleanup",
    "test_list_networks",
    "test_overlapping_networks",
    "test_public_and_private_networks",
]


def test_create_network(driver, network):
    """Network objects are opaque. For unit tests, some operations are
    supported.

    """
    assert len(network.addresses) == 254
    for addr in network.addresses:
        assert addr in network


def test_create_duplicate_netwoks(driver, network):
    """Networks with the same name may be created, as long as they are equal
    to those already created.

    """
    net2 = driver.ex_create_network(name=network.name, cidr=network.cidr)
    assert net2 == network

    with raises(LibcloudError) as exc:
        driver.ex_create_network(name=network.name, cidr=available_network())
    assert exc.value.value == ("Network '%s' already defined" %
                               (network.name,))


def test_destroy_network(driver):
    """Networks in use may not be destroyed.

    """
    network = driver.ex_create_network(name="net1", cidr=available_network())
    try:
        with sample_node(driver, networks=[network]):
            assert not driver.ex_destroy_network(network)

    finally:
        assert driver.ex_destroy_network(network)


def test_exhausted_networks(driver):
    """Networks cannot be over-allocated.

    """
    with sample_network(driver, "net1", cidr="172.16.0.0/30", public=True) as net:
        addr = net.allocate_address()
        assert str(addr.address) == "172.16.0.2"

        with raises(LibcloudError) as exc:
            addr = net.allocate_address()
        assert exc.value.value == "No more free addresses in 172.16.0.0/30"


def test_host_interface_cleanup(driver):
    """Host interfaces are removed when their associated networks are
    destroyed.

    """
    with sample_network(driver, "pub", public=True) as pub:
        with sample_node(driver, networks=[pub]):
            iface = pub.host_interface
            assert iface in netifaces.interfaces()
        assert iface in netifaces.interfaces()
    assert iface not in netifaces.interfaces()

    with sample_network(driver, "priv") as priv:
        with sample_node(driver, networks=[priv]):
            assert priv.host_interface is None


def test_list_networks(driver):
    """Networks are listed properly.

    """
    n_networks = len(driver.ex_list_networks())
    with sample_network(driver, "net1") as net1:
        networks = driver.ex_list_networks()
        assert len(networks) == n_networks + 1
        assert net1 in networks

        with sample_network(driver, "net2") as net2:
            networks = driver.ex_list_networks()
            assert len(networks) == n_networks + 2
            assert net1 in networks
            assert net2 in networks

        networks = driver.ex_list_networks()
        assert len(networks) == n_networks + 1
        assert net1 in networks
        assert net2 not in networks

    assert len(driver.ex_list_networks()) == n_networks


def test_overlapping_networks(driver):
    """Overlapping networks are not supported.

    """
    with sample_network(driver, "net1", cidr="172.16.0.0/24"):
        with raises(LibcloudError) as exc:
            driver.ex_create_network(name="net2",
                                     cidr="172.16.0.0/23")
        assert exc.value.value == "Network 'net2' overlaps with 'net1'"

        with raises(LibcloudError) as exc:
            driver.ex_create_network(name="net2",
                                     cidr="172.16.0.0/25")
        assert exc.value.value == "Network 'net2' overlaps with 'net1'"


def test_public_and_private_networks(driver, public_network, private_network):
    """Public networks are accessible (within the host), but private ones are
    not.

    """
    with sample_node(driver, networks=[public_network, private_network]) as n:
        assert len(n.public_ips) == 1
        assert ping(n.public_ips[0])
        assert len(n.private_ips) == 1
        assert not ping(n.private_ips[0])


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
