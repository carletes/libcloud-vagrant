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

"""Creates a node, and runs a provisioning script in it."""

import logging
import os
import sys

from libcloud.compute.deployment import ScriptDeployment
from libcloud.compute.providers import get_driver

from libcloudvagrant.driver import VAGRANT


cls = get_driver(VAGRANT)
driver = cls()

environ = dict(os.environ)
for k in ("http_proxy", "https_proxy", "no_proxy"):
    environ[k] = os.environ.get(k, "")

provision_script = ScriptDeployment("""#!/bin/sh

exec 2>&1

set -ex

sudo_run() {
    sudo env \
      http_proxy="%(http_proxy)s" \
      https_proxy="%(https_proxy)s" \
      no_proxy="%(no_proxy)s"\
        $*
}

sudo_run apt-get -y update
sudo_run apt-get -y install puppet
""" % environ)


LOG = logging.getLogger(os.path.basename(__file__))


def main():
    pub = driver.ex_create_network(name="pub",
                                   cidr=os.environ.get("LIBCLOUD_NETWORK",
                                                       "172.16.0.0/16"),
                                   public=True)

    precise64 = driver.get_image("hashicorp/precise64")

    size = driver.list_sizes()[0]

    LOG.info("Running provisioning script ...")
    node = driver.deploy_node(name="provision-node",
                              image=precise64,
                              size=size,
                              ex_networks=[pub],
                              deploy=provision_script)
    LOG.info("Provisioning status: %s", provision_script.exit_status)
    LOG.info("Provisioning output: %s", provision_script.stdout)

    LOG.info("Node '%s' running!", node.name)
    LOG.info("Log in with 'ssh vagrant@%s' (password: 'vagrant')",
             node.public_ips[0])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(message)s")
    sys.exit(main())
