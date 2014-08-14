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

"""Unit tests for nodes."""

import uuid

from libcloud.compute.types import NodeState

from libcloudvagrant.tests import sample_node


__all__ = [
    "test_create_node",
    "test_node_state",
]


def test_create_node(driver):
    """Nodes are created and registered correctly.

    """
    node_name = uuid.uuid4().hex
    assert node_name not in driver.list_nodes()

    with sample_node(driver) as node:
        assert node in driver.list_nodes()

        with driver._catalogue as c:
            assert node.id == c.virtualbox_uuid(node)


def test_node_state(driver):
    """Node state reflects actual VirtualBox status.

    """
    with sample_node(driver) as node:
        assert driver.ex_get_node_state(node) == NodeState.RUNNING

    assert driver.ex_get_node_state(node) == NodeState.UNKNOWN

    node.id = None
    assert driver.ex_get_node_state(node) == NodeState.UNKNOWN


def test_ssh(node):
    """The extension propery ``ssh_client`` implements an SSH client to the
    node.

    """
    with node.ex_ssh_client as ssh:
        stdout, stderr, rc = ssh.run("hostname")
        assert rc == 0
        assert stdout.strip() == node.name
        assert not stderr
