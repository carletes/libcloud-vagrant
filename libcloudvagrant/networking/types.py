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

"""Data types for the Vagrant networking driver."""

import logging

import ipaddr

from libcloud.common.types import LibcloudError
from libclod.networking.base import Network, Subnet

from libcloudvagrant.common.types import Serializable


__all__ = [
    "VagrantAddress",
    "VagrantNetwork",
]


class VagrantAddress(Serializable):

    """An IP address in a Vagrant network."""

    def __init__(self, address, network_name):
        self.address = ipaddr.IPAddress(address)
        self.network_name = network_name

    def to_dict(self):
        return {
            "address": str(self.address),
            "network_name": self.network_name,
        }

    def __hash__(self):
        return hash(self.address) ^ hash(self.network_name)


class VagrantSubnet(Subnet, Serializable):

    def __init__(self, name, cidr, driver):
        self._cidr = ipaddr.IPNetwork(cidr)
        ip_version = 4 if isinstance(self._cidr, ipaddr.IPv4Network) else 6
        super(VagrantSubnet, self).__init__(id=name,
                                            name=name,
                                            ip_version=ip_version,
                                            cidr=cidr,
                                            driver=driver)


class VagrantNetwork(Network, Serializable):

    """A Vagrant network."""

    log = logging.getLogger("libcloudvagrant")

    def __init__(self, name, cidr, public, allocated, host_interface, driver):
        extra = {
            "public": public,
            "host_interface": host_interface,
        }
        super(VagrantNetwork, self).__init__(id=name,
                                             name=name,
                                             extra=extra,
                                             driver=driver)
        self.name = name
        self.cidr = ipaddr.IPNetwork(cidr)
        self._allocated = set()
        for ip in allocated:
            self._allocate(VagrantAddress(ip, name))

    @property
    def addresses(self):
        """List of IP addresses in this network.

        :rtype: ``list`` of :class:`ipaddr.IPv4Address` or
                :class:`ipaddr.IPv6Address` objects

        """
        return list(self.cidr.iterhosts())

    @property
    def host_address(self):
        """Returns the host address of this network if it's a public one, or
        ``None`` if it's a private network.

        As of 1.6.3, Vagrant assigns the first IP address of the network to
        the host interface.

        """
        if self.public:
            return str(next(self.cidr.iterhosts()))

    @property
    def host_interface(self):
        return self.extra["host_interface"]

    @property
    def allocated(self):
        """Returns a list of allocated addresses for this network.

        :rtype: ``list`` of :class:`.VagrantAddress` objects.

        """
        return list(self._allocated)

    @property
    def public(self):
        return self.extra["public"]

    def allocate_address(self):
        """Allocates an address in this network.

        Raises an error if no more addresses can be allocated.

        :return: The allocated address
        :rtype:  :class:`.VagrantAddress`

        """
        allocated = set(self._allocated)
        if self.public:
            allocated.add(VagrantAddress(self.host_address, self.name))
        self.log.debug("allocate_address(): Allocated: %s", allocated)

        for h in self.cidr.iterhosts():
            address = VagrantAddress(h, self.name)
            self.log.debug("allocate_address(): Trying %s", address)
            if address not in allocated:
                self.log.debug("allocate_address(): %s is available", address)
                return self._allocate(address)
        raise LibcloudError("No more free addresses in %s" % (self.cidr,))

    def _allocate(self, address):
        self._allocated.add(address)
        return address

    def deallocate_address(self, address):
        """Deallocates the given address in this network.

        :param address: The address to deallocate
        :type address:  :class:``ipaddr.IPv4Address` or
                        :class:`ipaddr.IPv6Address`

        """
        self.log.debug("deallocate_address(): Allocated: %s", self.allocated)
        for addr in self._allocated:
            if addr.address == address:
                self._allocated.remove(addr)
                self.log.debug("deallocate_address(): %s deallocated", address)
                break
        self.log.debug("deallocate_address(): Allocated: %s", self.allocated)

    def to_dict(self):
        allocated = []
        for addr in self._allocated:
            params = addr.to_dict()
            del params["network_name"]
            allocated.append(params)
        return {
            "name": self.name,
            "cidr": str(self.cidr),
            "public": self.public,
            "allocated": sorted([str(ip.address) for ip in self._allocated]),
            "host_interface": self.host_interface,
        }

    def __contains__(self, other):
        return other in self.cidr
