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

import subprocess

from libcloudvagrant.tests import new_driver, sample_node


__all__ = [
    "test_num_cpus",
]


def test_num_cpus():
    """The Vagrant driver honours the number of CPUs expressed in the nodes'
    size objects.

    """
    driver = new_driver()

    size = driver.list_sizes()[0]
    size.extra["cpus"] = 1
    with sample_node(size=size) as node:
        assert num_cpus(node) == 1

    size.extra["cpus"] = 2
    with sample_node(size=size) as node:
        assert num_cpus(node) == 2


def num_cpus(node):
    driver = new_driver()

    ssh = driver._vagrant_ssh_config(node.name)
    ssh["opts"] = " ".join([
        "-o 'StrictHostKeyChecking no'",
        "-o 'UserKnownHostsFile /dev/null'",
    ])
    ssh["cmd"] = "cat /proc/cpuinfo | grep processor | wc -l"

    cmd = "ssh -p %(port)s -i %(key)s %(opts)s %(user)s@%(host)s %(cmd)s" % ssh
    p = subprocess.Popen(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode:
        raise Exception(stderr)
    return int(stdout.strip())
