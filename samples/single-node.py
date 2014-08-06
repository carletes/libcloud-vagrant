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

"""Creates a single node."""

import logging
import os
import sys

from libcloud.compute import providers as compute_providers
from libcloud.networking import providers as network_providers
from libcloud.networking.base import Network, Subnet

from libcloudvagrant import VAGRANT


compute_driver = compute_providers.get_driver(VAGRANT)()
network_driver = network_providers.get_driver(VAGRANT)()

LOG = logging.getLogger(os.path.basename(__file__))


def main():
    pub = network_driver.create_network(Network(name="pub",
                                                extra={"public": True}))
    cidr = os.environ.get("LIBCLOUD_NETWORK", "172.16.0.0/16")
    pub.create_subnets([Subnet(cidr=cidr)])
    node_ip = network_driver.create_floating_ip(pub)

    precise64 = compute_driver.get_image("hashicorp/precise64")

    size = compute_driver.list_sizes()[0]
    size.ram = 1024
    size.extra["cpus"] = 2

    node = compute_driver.create_node(name="single-node",
                                      image=precise64,
                                      size=size)
    network_driver.attach_floating_ip_to_node(node, node_ip)

    for volume in compute_driver.list_volumes():
        if volume.name == "srv_data":
            srv_data = volume
            break
    else:
        srv_data = compute_driver.create_volume(name="srv_data", size=10)

    if srv_data.attached_to is None:
        assert not srv_data.attach(node)

        # XXX Context manager for this?
        compute_driver.ex_stop_node(node)
        assert srv_data.attach(node)
        compute_driver.ex_start_node(node)

    LOG.info("Node '%s' running!", node.name)
    LOG.info("Log in with 'ssh vagrant@%s' (password: 'vagrant')",
             node.public_ips[0])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(message)s")
    sys.exit(main())
