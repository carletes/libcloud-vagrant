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

"""Unit tests for Vagrant-specific extensions."""

from libcloudvagrant.tests import new_driver, sample_node


__all__ = [
    "test_num_cpus",
]


driver = new_driver()


def test_num_cpus():
    """The Vagrant driver honours the number of CPUs expressed in the nodes'
    size objects.

    """
    size = driver.list_sizes()[0]
    size.extra["cpus"] = 1
    with sample_node(size=size) as node:
        assert num_cpus(node) == 1

    size.extra["cpus"] = 2
    with sample_node(size=size) as node:
        assert num_cpus(node) == 2


def num_cpus(node):
    count = "cat /proc/cpuinfo | grep processor | wc -l"
    with node.ex_ssh_client as ssh:
        stdout, stderr, rc = ssh.run(count)
        if rc:
            raise Exception(stderr)
        return int(stdout.strip())
