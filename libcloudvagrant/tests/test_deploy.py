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

import uuid

from contextlib import contextmanager

from libcloud.compute.deployment import ScriptDeployment


__all__ = [
    "test_deploy_without_network",
    "test_http_proxy",
    "test_with_private_network",
    "test_with_public_network",
]


def test_deploy_without_network(driver):
    """Deployment works for nodes without networks.

    """
    with deploy_node(driver, networks=[]):
        pass


def test_http_proxy(driver):
    """Deploying behind an HTTP proxy works.

    """
    script = """#!/bin/sh
    echo "Hello from $(hostname)"
    wget -O - https://github.com/carletes/libcloud-vagrant
    """
    with deploy_node(driver, script=script) as result:
        assert ("you could prototype a small cluster" in result)


def test_with_private_network(driver, private_network):
    """Deployment works for nodes with private networks.

    """
    with deploy_node(driver, networks=[private_network]):
        pass


def test_with_public_network(driver, public_network):
    """Deployment works for nodes with public networks.

    """
    with deploy_node(driver, networks=[public_network]):
        pass


@contextmanager
def deploy_node(driver, networks=None, script=None):
    script = script or """#!/bin/sh

    echo "Hello from $(hostname)"
    """
    script = ScriptDeployment(script)
    name = uuid.uuid4().hex
    node = driver.deploy_node(name=name,
                              image=driver.get_image("hashicorp/precise64"),
                              size=driver.list_sizes()[0],
                              ex_networks=networks,
                              deploy=script)
    try:
        assert node.name == name
        assert script.exit_status == 0, script.stderr
        expected = "Hello from %s" % (node.name,)
        assert (expected in script.stdout), script.stdout
        yield script.stdout
    finally:
        driver.destroy_node(node)
