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

"""Data types for the Vagrant compute driver."""

from libcloud.compute import base
from libcloud.compute.types import NodeState

from libcloudvagrant.common.types import Serializable
from libcloudvagrant.networking.types import VagrantAddress


__all__ = [
    "VagrantImage",
    "VagrantNode",
    "VagrantNodeSize",
    "VagrantVolume",
]


class VagrantImage(base.NodeImage, Serializable):

    """A Vagrant image.

    Differences from ``NodeImage``:

    * The image ID is optional, and defaults to the value of the image name.

    """

    def __init__(self, name, driver):
        super(VagrantImage, self).__init__(id=name,
                                           name=name,
                                           driver=driver)

    def to_dict(self):
        return {
            "name": self.name,
        }

    def __repr__(self):
        fields = ("%s=%s" % (k, v) for (k, v) in self.to_dict().items())
        return "VagrantImage(%s)" % (" ".join(fields),)


class VagrantNode(base.Node, Serializable):

    def __init__(self, id, name, public_ips, private_ips, size, image, driver):
        self._public_ips = [VagrantAddress(**p) for p in public_ips]
        self._private_ips = [VagrantAddress(**p) for p in private_ips]
        size = VagrantNodeSize.from_dict(driver=driver, **size)
        image = VagrantImage.from_dict(driver=driver, **image)
        super(VagrantNode, self).__init__(id=id,
                                          name=name,
                                          state=NodeState.UNKNOWN,
                                          public_ips=self.public_ips,
                                          private_ips=self.private_ips,
                                          driver=driver,
                                          size=size,
                                          image=image)

    def state():
        def fget(self):
            try:
                return self.driver.ex_get_node_state(self)
            except:
                return NodeState.UNKNOWN

        def fset(self, _):
            pass

        return locals()

    state = property(**state())

    def public_ips():
        def fget(self):
            return [str(ip.address) for ip in self._public_ips]

        def fset(self, _):
            pass

        return locals()

    public_ips = property(**public_ips())

    def private_ips():
        def fget(self):
            return [str(ip.address) for ip in self._private_ips]

        def fset(self, _):
            pass

        return locals()

    private_ips = property(**private_ips())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "public_ips": [
                {"address": str(ip.address), "network_name": ip.network_name}
                for ip in self._public_ips
            ],
            "private_ips": [
                {"address": str(ip.address), "network_name": ip.network_name}
                for ip in self._private_ips
            ],
            "size": self.size.to_dict(),
            "image": self.image.to_dict(),
        }

    def __repr__(self):
        fields = ("%s=%s" % (k, v) for (k, v) in self.to_dict().items())
        return "VagrantNode(%s)" % (" ".join(fields),)

    @property
    def ex_ssh_client(self):
        """Returns a context manager implementing an SSH client connected to
        this node.

        This is an extension attribute.

        The SSH connection to this node will be opened before the flow enters
        the context, and closed before it leaves.

        """
        return self.driver.ex_ssh_client(self)


class VagrantNodeSize(base.NodeSize, Serializable):

    """Node size class for Vagrant nodes.

    Differences with the base ``NodeSize`` class:

        * Parameter ``id`` is optional, and defaults to the value of parameter
          ``name``.

        * Parameter ``disk`` is ignored, since it's defined by the size of the
          node image.

        * Parameter ``bandwidth`` is ignored, since bandwidth limitations are
          not enforced.

        * Parameter ``price`` is ignored, since nodes are free.

        * An ``extra`` parameter called ``cpus`` is accepted, representing the
          number of CPUs in a node.

    """

    def __init__(self, name, ram, driver, id=None, extra=None, **kwargs):
        """
        :param id: Size ID (optional, defaults to ``name``).
        :type  id: ``str``

        :param name: Size name.
        :type  name: ``str``

        :param ram: Amount of memory (in MB) provided by this size.
        :type  ram: ``int``

        :param driver: Driver this size belongs to.
        :type  driver: :class:`VagrantNodeDriver`

        :param extra: Optional provider specific attributes associated with
                      this size.

                      Accepted keys:

                          ``cpus``
                             Number of CPUs. Defaults to 1.

        :type  extra: ``dict``

        """
        super(VagrantNodeSize, self).__init__(id=id and id or name,
                                              name=name,
                                              ram=ram,
                                              disk=0,
                                              bandwidth=0,
                                              price=0,
                                              driver=driver,
                                              extra=extra)
        self.extra.setdefault("cpus", 1)

    @classmethod
    def from_dict(cls, **params):
        return cls(name=params["name"],
                   ram=params["ram"],
                   driver=params["driver"],
                   extra={"cpus": params["cpus"]})

    def to_dict(self):
        return {
            "name": self.name,
            "ram": self.ram,
            "cpus": self.extra["cpus"],
        }

    def __repr__(self):
        fields = ("%s=%s" % (k, v) for (k, v) in self.to_dict().items())
        return "VagrantNodeSize(%s)" % (" ".join(fields),)


class VagrantVolume(base.StorageVolume, Serializable):

    """Storage volume class for Vagrant nodes.

    Differences with the base ``StorageVolume`` class:

        * Parameter ``id`` is optional, and defaults to the value of parameter
          ``name``.

        * An ``extra`` parameter called ``attached_to`` is accepted, pointing
          to the node this volume is attached to.

        * An ``extra`` parameter called ``path`` is accepted, pointing to the
          file system location of this volume in the host system.

    """

    def __init__(self, name, size, driver, id=None, extra=None):
        """
        :param id: Storage volume ID (optional, defaults to the value of ``name``).
        :type id: ``str``

        :param name: Storage volume name.
        :type name: ``str``

        :param size: Size of this volume (in GB).
        :type size: ``int``

        :param driver: Driver this image belongs to.
        :type driver: :class:`VagrantNodeDriver`

        :param extra: Optional provider specific attributes.

                      Accepted keys:

                        ``attached_to``
                          Name of the node this volume is attached to, or
                          ``None`` for detached volumes. Defaults to ``None``.

                        ``path``
                          Path to the file system location of this volume in
                          the host system.

        :type extra: ``dict``

        """
        super(VagrantVolume, self).__init__(id=name,
                                            name=name,
                                            size=size,
                                            extra=extra,
                                            driver=driver)
        if extra is None:
            extra = {}
        self.attached_to = extra.get("attached_to")
        self.path = extra.get("path")

    @classmethod
    def from_dict(cls, **params):
        return cls(name=params["name"],
                   size=params["size"],
                   extra={
                       "attached_to": params["attached_to"],
                       "path": params["path"],
                   },
                   driver=params["driver"],)

    def to_dict(self):
        return {
            "name": self.name,
            "size": self.size,
            "attached_to": self.attached_to,
            "path": self.path,
        }

    def __repr__(self):
        fields = ("%s=%s" % (k, v) for (k, v) in self.to_dict().items())
        return "VagrantVolume(%s)" % (" ".join(fields),)
