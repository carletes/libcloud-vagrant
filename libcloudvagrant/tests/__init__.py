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

"""Unit test support code."""

import logging
import uuid

from contextlib import contextmanager

import ipaddr
import netifaces


__all__ = [
    "available_network",
    "sample_network",
    "sample_node",
    "sample_volume",
]


LOG = logging.getLogger("libcloudvagrant")


ALLOCATED_NETWORKS = set()


def available_network():
    """Returns the first available 24-bit available network in the range of
    the 256 networks in the block 192.168/16.

    """
    local_networks = local_rfc1918_networks()
    base = ipaddr.IPNetwork("192.168.0.0/24")
    for n in base.supernet(prefixlen_diff=8).iter_subnets(prefixlen_diff=8):
        if str(n) in ALLOCATED_NETWORKS:
            continue
        if any(n.overlaps(localnet) for localnet in local_networks):
            continue
        else:
            ALLOCATED_NETWORKS.add(str(n))
            return n
    raise Exception("No available 24-bit network in the block 192.168/16")


@contextmanager
def sample_network(driver, name=None, cidr=None, public=False):
    """Context manager which creates a new network before starting, and
    destroys it after leaving.

    """
    name = name or uuid.uuid4().hex
    cidr = cidr or str(available_network())
    network = driver.ex_create_network(name, cidr, public)
    try:
        yield network
    finally:
        try:
            ALLOCATED_NETWORKS.remove(str(network))
        except KeyError:
            pass
        driver.ex_destroy_network(network)


@contextmanager
def sample_node(driver, name=None, networks=None, size=None):
    """Context manager which creates a new node before starting, and destroys
    it after leaving.

    The node is based on the ``hashicorp/precise64`` Vagrant image.

    """
    node = driver.create_node(name=name or uuid.uuid4().hex,
                              size=size or driver.list_sizes()[0],
                              image=driver.get_image("hashicorp/precise64"),
                              ex_networks=networks or [])
    try:
        yield node
    finally:
        node.destroy()


@contextmanager
def sample_volume(driver, name=None):
    """Context manager which creates a new 1 GB volume before starting, and
    destroys it after leaving.

    """
    volume = driver.create_volume(name=name or uuid.uuid4().hex, size=1)
    try:
        yield volume
    finally:
        driver.detach_volume(volume)
        volume.destroy()


def local_rfc1918_networks():
    ret = []
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
        for addr in addrs:
            addr = ipaddr.IPNetwork("%(addr)s/%(netmask)s" % addr)
            if addr.is_private:
                ret.append(addr.masked())
    return ret
