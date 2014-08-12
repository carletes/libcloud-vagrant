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

"""Creates a two-node cluster."""

import logging
import os
import sys

from libcloud.compute.providers import get_driver

from libcloudvagrant import VAGRANT


cls = get_driver(VAGRANT)
driver = cls()

LOG = logging.getLogger(os.path.basename(__file__))


def main():
    pub_network = os.environ.get("LIBCLOUD_PUBLIC_NETWORK", "172.16.0.0/16")
    priv_network = os.environ.get("LIBCLOUD_PRIVATE_NETWORK", "172.17.0.0/16")

    pub = driver.ex_create_network(name="pub", cidr=pub_network, public=True)
    priv = driver.ex_create_network(name="priv", cidr=priv_network)

    precise64 = driver.get_image("hashicorp/precise64")

    size = driver.list_sizes()[0]

    node1 = driver.create_node(name="cluster-node-1",
                               image=precise64,
                               size=size,
                               ex_networks=[pub, priv])

    node2 = driver.create_node(name="cluster-node-2",
                               image=precise64,
                               size=size,
                               ex_networks=[priv])

    LOG.info("Node '%s' running!", node1.name)
    LOG.info("Node '%s' running!", node2.name)

    LOG.info("Log in to '%s' with 'ssh vagrant@%s' (password: 'vagrant')",
             node1.name, node1.public_ips[0])
    LOG.info("From '%s' you may log in to '%s' with "
             "'ssh vagrant@%s' (password: 'vagrant')",
             node1.name, node2.name, node2.private_ips[0])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(message)s")
    sys.exit(main())
