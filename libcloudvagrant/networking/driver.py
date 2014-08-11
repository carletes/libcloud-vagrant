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

"""Apache Libcloud networking driver implementation for Vagrant."""

import logging
import os
import pwd

from libcloud.networking.base import NetworkingDriver

from libcloudvagrant.common import virtualbox
from libcloudvagrant.common.types import VAGRANT, VagrantCatalogue
from libcloudvagrant.networking.types import VagrantNetwork


__all__ = [
    "VagrantDriver",
]


_HOME = pwd.getpwuid(os.getuid()).pw_dir


class VagrantDriver(NetworkingDriver):

    """Apache Libcloud driver implementation.

    Docstrings here document how this driver diverges from the base class.

    """

    type = VAGRANT
    name = "Vagrant"
    website = "http://www.vagrantup.com/"

    log = logging.getLogger("libcloudvagrant")

    def __init__(self):
        super(VagrantDriver, self).__init__(key=None)

    def create_network(self, network, subnet=None):
        """Creates a Vagrant network.

        The ``subnet`` parameter is required. A ``ValueError`` will be raised
        if it's not given.

        :param network: Network object with at least 'name' filled in
        :type network: :class:`Network`

        :param subnet: Subnet to attach to the network.
        :type subnet: :class:`Subnet`

        """
        self.log.debug("create_network(%s, %s): Entering", network, subnets)

        if subnet is None:
            raise ValueError("No subnet specified")

        with self._catalogue as c:
            public = network.get("extra", {"public": False})["public"]
            network = VagrantNetwork(name=network.name,
                                     cidr=subnet.cidr,
                                     public=public,
                                     allocated=[],
                                     host_interface=None)
            c.add_network(network)
            return network

    def delete_network(self, network):
        """Destroys a Vagrant network object.

        Networks with addresses in use by nodes cannot be destroyed.

        :param network: Existing Network object with at least 'id' filled in
        :type network:  :class:`VagrantNetwork`

        :return: ``True`` on success, ``False`` otherwise
        :rtype:  ``Bool``

        """
        self.log.info("Destroying network '%s' ..", network)
        try:
            with self._catalogue as c:
                ifname = network.host_interface
                self.log.debug("destoy_network(%s): Iface: %s",
                               network.name, ifname)
                if ifname is not None:
                    virtualbox.destroy_host_interface(ifname)
                c.remove_network(network)
                return True
            self.log.info(".. Network '%s' destroyed", network.name)
        except:
            self.log.warn("Cannot destroy network %s", network, exc_info=True)
            return False

    def list_networks(self):
        """Returns a list of all defined Vagrant networks.

        :rtype: ``list`` of :class:`VagrantNetwork`

        """
        with self._catalogue as c:
            return c.get_networks()

    @property
    def _dot_libcloudvagrant(self):
        """Path to the Vagrant catalogue directory.

        """
        dname = os.path.join(_HOME, ".libcloudvagrant")
        if not os.access(dname, os.F_OK):
            os.mkdir(dname)
        return dname

    @property
    def _catalogue(self):
        """Vagrant catalogue instance.

        """
        return VagrantCatalogue(self._dot_libcloudvagrant, self)
