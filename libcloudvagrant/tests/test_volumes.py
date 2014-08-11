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

"""Unit tests for volumes."""

import uuid

from libcloud.compute.types import NodeState
from libcloudvagrant.tests import sample_node, sample_volume


__all__ = [
    "test_attach_to_device",
    "test_attach_volume",
    "test_create_volume",
    "test_destroy_volume",
    "test_invalid_device",
    "test_move_volume",
]


def test_attach_to_device(driver, node):
    """It is possible to attach volumes to specific devices.

    """
    with sample_volume(driver) as v1, sample_volume(driver) as v2:
        assert driver.attach_volume(node, v1, device="/dev/sdc")
        assert not driver.attach_volume(node, v2, device="/dev/sdc")
        assert driver.attach_volume(node, v2, device="/dev/sdb")


def test_attach_volume(driver, node, volume):
    """Volumes may be hot-plugged to nodes.

    """
    assert node.state == NodeState.RUNNING
    assert volume.attached_to is None
    assert driver.attach_volume(node, volume)
    assert volume.attached_to == node.name


def test_move_volume(driver, volume):
    """Attached volumes may be detached and attached to anothe node.

    """
    with sample_node(driver) as n1, sample_node(driver) as n2:
        assert driver.attach_volume(n1, volume)
        assert volume.attached_to == n1.name
        assert not driver.attach_volume(n2, volume)

        assert driver.detach_volume(volume)
        assert volume.attached_to is None
        assert driver.attach_volume(n2, volume)
        assert volume.attached_to == n2.name
        assert not driver.attach_volume(n1, volume)


def test_create_volume(driver):
    """Created volumes are correctly registered.

    """
    test_volume = uuid.uuid4().hex
    assert test_volume not in driver.list_volumes()

    size = 42
    volume = driver.create_volume(size=size, name=test_volume)
    assert volume.name == test_volume
    assert volume.size == size
    assert volume in driver.list_volumes()


def test_destroy_volume(driver, volume):
    """Attached volumes may not be destroyed.

    """
    volume.attached_to = "some-node"
    assert not driver.destroy_volume(volume)

    volume.attached_to = None
    assert driver.destroy_volume(volume)
    assert volume not in driver.list_volumes()


def test_invalid_device(driver, node, volume):
    """Volumes may only be attached to ``/dev/sd[a-z]``.

    """
    assert not driver.attach_volume(node, volume, "/dev/sdB")
    assert driver.attach_volume(node, volume, "/dev/sdb")
