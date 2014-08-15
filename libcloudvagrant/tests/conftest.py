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

"""py.text fixtures"""

import itertools
import logging
import tempfile
import pprint

import netifaces

import pytest

from libcloud.compute import providers

from libcloudvagrant import VAGRANT

from libcloudvagrant.tests import sample_network, sample_node, sample_volume


__all__ = [
    "driver",
    "network",
    "node",
    "private_network",
    "public_network",
    "volume",
]


logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(name)s %(message)s")


@pytest.yield_fixture(scope="session")
def driver(request):
    """Return a new driver instance, backed by a temporary directory. This
    driver instance will be used for all unit tests.

    """
    d = providers.get_driver(VAGRANT)()
    d._home = tempfile.mkdtemp(prefix="libcloudvagrant-home-")
    try:
        yield d
    finally:
        rem = list(itertools.chain(d.list_nodes(), d.list_volumes()))
        if rem:
            raise AssertionError("Remaining objects: %s" %
                                 (pprint.pformat(rem),))

        # XXX Revisit this
        ifaces = netifaces.interfaces()
        rem = [n for n in d.ex_list_networks() if n.host_interface in ifaces]
        if rem:
            raise AssertionError("Remaining objects: %s" %
                                 (pprint.pformat(rem),))


@pytest.yield_fixture(scope="session")
def node(driver):
    """Return an ephemeral Ubuntu 12.04 node.

    """
    with sample_node(driver) as n:
        yield n


@pytest.yield_fixture(scope="session")
def private_network(driver):
    """Return an ephemeral private network.

    """
    with sample_network(driver, public=False) as n:
        yield n


network = private_network


@pytest.yield_fixture(scope="session")
def public_network(driver):
    """Return an ephemeral private network.

    """
    with sample_network(driver, public=True) as n:
        yield n


@pytest.yield_fixture(scope="function")
def volume(driver):
    """Return an ephemeral 1 GB volume.

    """
    with sample_volume(driver) as v:
        try:
            yield v
        finally:
            driver.detach_volume(v)
