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

import uuid

import pytest

from libcloudvagrant.tests import new_driver


__all__ = [
    "driver",
    "node",
    "volume",
]


@pytest.fixture
def driver():
    """Return a new driver instance, backed by a temporary directory.

    """
    return new_driver()


@pytest.yield_fixture
def node():
    """Return an ephemeral Ubuntu 12.04 node.

    """
    d = new_driver()
    node = d.create_node(name=uuid.uuid4().hex,
                         size=d.list_sizes()[0],
                         image=d.get_image("hashicorp/precise64"))
    try:
        yield node
    finally:
        node.destroy()


@pytest.yield_fixture
def volume():
    """Return an ephemeral 1 GB volume.

    """
    d = new_driver()
    volume = d.create_volume(name=uuid.uuid4().hex, size=1)
    try:
        yield volume
    finally:
        volume.destroy()
