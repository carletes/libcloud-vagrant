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

import tempfile
import uuid

from libcloud.compute import providers

from libcloudvagrant.driver import VAGRANT


__all__ = [
    "new_driver",
    "sample_network",
    "sample_node",
    "sample_volume",
]


import libcloudvagrant.driver
libcloudvagrant.driver._HOME = tempfile.mkdtemp(prefix="libcloudvagrant-home-")


def new_driver():
    """Returns a new instance of the Vagrant compute driver.

    """
    return providers.get_driver(VAGRANT)()


class sample_network(object):

    """Context manager which creates a new network before starting, and
    destroys it after leaving.

    """

    def __init__(self, name, cidr, public=False):
        self.name = name
        self.cidr = cidr
        self.public = public
        self._network = None

    def __enter__(self):
        d = new_driver()
        self._network = d.ex_create_network(self.name, self.cidr, self.public)
        return self._network

    def __exit__(self, *exc_info):
        d = new_driver()
        d.ex_destroy_network(self._network)
        self._network = None


class sample_node(object):

    """Context manager which creates a new node before starting, and destroys
    it after leaving.

    The node is based on the ``hashicorp/precise64`` Vagrant image.

    """

    def __init__(self, name=None, networks=None, size=None):
        self.name = name and name or uuid.uuid4().hex
        self.networks = networks and networks or []
        self.size = size
        self._node = None

    def __enter__(self):
        d = new_driver()
        image = d.get_image("hashicorp/precise64")
        size = self.size or d.list_sizes()[0]
        self._node = d.create_node(name=self.name,
                                   size=size,
                                   image=image,
                                   ex_networks=self.networks)
        return self._node

    def __exit__(self, *exc_info):
        self._node.destroy()
        self._node = None


class sample_volume(object):

    """Context manager which creates a new 1 GB volume before starting, and
    destroys it after leaving.

    """

    def __init__(self, name=None):
        self.name = name and name or uuid.uuid4().hex
        self._volume = None

    def __enter__(self):
        d = new_driver()
        self._volume = d.create_volume(size=1, name=self.name)
        return self._volume

    def __exit__(self, *exc_info):
        self._volume.destroy()
        self._volume = None
