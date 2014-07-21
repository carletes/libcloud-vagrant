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

"""Unit tests for deployment."""

from libcloud.compute.deployment import ScriptDeployment

from libcloudvagrant.tests import new_driver, sample_network, sample_node


__all__ = [
    "test_deploy_without_network",
    "test_with_private_network",
    "test_with_public_network",
]


driver = new_driver()


def test_deploy_without_network():
    """Deployment works for nodes without networks.

    """
    with sample_node() as node:
        deploy_node(node)


def test_with_private_network():
    """Deployment works for nodes with private networks.

    """
    with sample_network("priv", "172.16.0.0/16", public=False) as net:
        with sample_node(networks=[net]) as node:
            deploy_node(node)


def test_with_public_network():
    """Deployment works for nodes with public networks.

    """
    with sample_network("priv", "172.16.0.0/16", public=True) as net:
        with sample_node(networks=[net]) as node:
            deploy_node(node)


def deploy_node(node):
    script = ScriptDeployment("""#!/bin/sh

    echo "Hello from $(hostname)"
    """)

    n = driver.deploy_node(name=node.name,
                           image=node.image,
                           size=node.size,
                           deploy=script)
    assert n.name == node.name
    assert script.exit_status == 0
    assert script.stdout == "Hello from %s\n" % (node.name,), script.stdout
