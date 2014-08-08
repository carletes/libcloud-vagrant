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

from libcloudvagrant.tests import new_driver, sample_node


__all__ = [
    "test_create_node",
]


driver = new_driver()


def test_create_node():
    """Nodes are created and registered correctly.

    """
    node_name = uuid.uuid4().hex
    assert node_name not in driver.list_images()

    image = driver.get_image("hashicorp/precise64")
    size = driver.list_sizes()[0]
    node = driver.create_node(node_name, size=size, image=image)
    try:
        assert node in driver.list_nodes()

        with driver._catalogue as c:
            assert node.id == c.virtualbox_uuid(node)
    finally:
        driver.destroy_node(node)


def test_ssh():
    """The extension propery ``ssh_client`` implements an SSH client to the
    node.

    """
    with sample_node() as node:
        with node.ex_ssh_client as ssh:
            stdout, stderr, rc = ssh.run("hostname")
            assert rc == 0
            assert stdout.strip() == node.name
            assert not stderr
