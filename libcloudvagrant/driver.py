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

"""Apache Libcloud compute driver implementation for Vagrant."""

import itertools
import logging
import os
import pwd
import re
import subprocess
import time

from contextlib import contextmanager

try:
    import paramiko
    _ = paramiko  # For pyflakes
except ImportError:
    from libcloud.compute.ssh import ShellOutSSHClient as SSHClient
else:
    from libcloud.compute.ssh import ParamikoSSHClient as SSHClient

from libcloud.common.types import LibcloudError
from libcloud.compute import base
from libcloud.compute.types import DeploymentError, NodeState

from libcloudvagrant import virtualbox
from libcloudvagrant.catalogue import VagrantCatalogue
from libcloudvagrant.types import (
    VagrantImage,
    VagrantNetwork,
    VagrantNode,
    VagrantNodeSize,
    VagrantVolume,
)


__all__ = [
    "VAGRANT",
    "VagrantDriver",
]


VAGRANT = "vagrant"

_HOME = pwd.getpwuid(os.getuid()).pw_dir

# ``NODE_ONLINE_WAIT_TIMEOUT`` and ``SSH_CONNECT_TIMEOUT`` are needed in our
# reimplementation of ``deploy_node``,
#
# They're not part of the API exposed in ``libcloud.compute.base``, so we
# provide fallback values, in case they get removed in the future
try:
    NODE_ONLINE_WAIT_TIMEOUT = base.NODE_ONLINE_WAIT_TIMEOUT
except AttributeError:
    NODE_ONLINE_WAIT_TIMEOUT = 10 * 60

try:
    SSH_CONNECT_TIMEOUT = base.SSH_CONNECT_TIMEOUT
except AttributeError:
    SSH_CONNECT_TIMEOUT = 5 * 60


class VagrantDriver(base.NodeDriver):

    """Apache Libcloud driver implementation.

    Docstrings here document how this driver diverges from the base class.

    """

    type = VAGRANT
    name = "Vagrant"
    website = "http://www.vagrantup.com/"

    log = logging.getLogger("libcloudvagrant")

    def __init__(self):
        super(VagrantDriver, self).__init__(key=None)

    def attach_volume(self, node, volume, device=None):
        """Attaches volume to node.

        At the moment only SATA devices of the form ``/dev/sd[a-z]`` are
        accepted as values to parameter ``device``.

        :param node: Node to attach volume to.
        :type node: :class:`VagrantNode`

        :param volume: Volume to attach.
        :type volume: :class:`VagrantVolume`

        :param device: Where the device is exposed, e.g. '/dev/sdb'
        :type device: ``str``

        :rytpe: ``bool``

        """
        if volume.attached_to:
            self.log.warn("Volume %s already attached to %s",
                          volume.name, volume.attached_to)
            return False

        try:
            with self._catalogue as c:
                virtualbox.attach_volume(node.id, volume.path, device)
                volume.attached_to = node.name
                c.update_volume(volume)
        except:
            self.log.warn("Error attaching %s to %s", volume, node,
                          exc_info=True)
            return False
        self.log.info("Volume '%s' attached to node '%s'",
                      volume.name, node.name)
        return True

    def create_node(self, name, size, image, ex_networks=None, **kwargs):
        """Create a new node instance. This instance will be started
        automatically.

        Requires the following arguments:

        :param name:   String with a name for this new node
        :type name:   ``str``

        :param size:   The size of resources allocated to this node.
        :type size:   :class:`VagrantSize`

        :param image:  OS Image to boot on node.
        :type image:  :class:`VagrantImage`

        Accepts the following non-standard arguments:

        :param ex_networks: The networks to connect this node to.
        :type ex_networks:  ``list`` of :class:`VagrantNetwork`

        All other arguments are ignored.

        """
        if ex_networks is None:
            networks = []
        else:
            networks = ex_networks

        self.log.info("Creating node '%s' ..", name)

        with self._catalogue as c:
            public_ips = [n.allocate_address().to_dict()
                          for n in networks if n.public]
            private_ips = [n.allocate_address().to_dict()
                           for n in networks if not n.public]
            size = size.to_dict()
            image = image.to_dict()
            for n in networks:
                c.update_network(n)
            node = VagrantNode(id=None,
                               name=name,
                               public_ips=public_ips,
                               private_ips=private_ips,
                               driver=self,
                               size=size,
                               image=image)
            self.log.debug("create_node(%s): Created object: %s", name, node)
            c.add_node(node)
            c.save()  # Explicit save, so that the next command succeeds
            self.ex_start_node(node)
            self.log.info(".. Node '%s' created", name)

            node.id = c.virtualbox_uuid(node)
            c.add_node(node)
            c.save()

            public_networks = filter(lambda n: n.public, networks)
            self.log.debug("create_node(%s): Public networks: %s",
                           name, public_networks)
            if public_networks:
                ifaces = virtualbox.get_host_interfaces(node.id)
                self.log.debug("create_node(%s): Ifaces: %s", name, ifaces)
                for n, iface in zip(public_networks, ifaces):
                    self.log.debug("create_node(%s): Iface for '%s': '%s'",
                                   name, n.name, iface)
                    n.host_interface = iface
                    c.update_network(n)

            return node

    def create_volume(self, size, name, **kwargs):
        """Create a new volume.

        :param size: Size of volume in gigabytes (required)
        :type size: ``int``

        :param name: Name of the volume to be created
        :type name: ``str``

        All other arguments are ignored.

        :return: The newly created volume.
        :rtype: :class:`VagrantVolume`

        """
        with self._catalogue as c:
            path = c.volume_path("%s.vdi" % (name,))
            virtualbox.create_volume(path=path, size=size * 1024)
            volume = VagrantVolume(name=name,
                                   size=size,
                                   extra={
                                       "attached_to": None,
                                       "path": path,
                                   },
                                   driver=self)
            c.add_volume(volume)
            self.log.info("Volume '%s' created", name)
            return volume

    def delete_image(self, image):
        """Deletes a node image from a provider.

        :param image: Node image object.
        :type image:  :class:`VagrantImage`

        :return: ``True`` if delete_image was successful, ``False`` otherwise.
        :rtype: ``bool``

        """
        with self.catalogue:
            try:
                self._vagrant("box remove --force --provider virtualbox",
                              image.id)
                return True
            except:
                self.log.warn("Cannot remove image %s", image, exc_info=True)
                return False

    def deploy_node(self, **kwargs):
        """Create a new node, and start deployment.

        This function may raise a :class:`DeploymentException`, if a
        create_node call was successful, but there is a later error (like SSH
        failing or timing out).  This exception includes a Node object which
        you may want to destroy if incomplete deployments are not desirable.

        We use ``vagrant ssh-config <node>`` in order to get the SSH
        connection parameters for the deployment task. In order to do that,
        the node must be created first.

        The base implementation makes use of the SSH connection parameters
        *before* creating the node. Therefore we have to override it.

        :param deploy: Deployment to run once machine is online and available
                       to SSH.
        :type deploy: :class:`Deployment`

        :param ssh_timeout: Optional SSH connection timeout in seconds
                            (default is 10).
        :type ssh_timeout: ``float``

        :param timeout: How many seconds to wait before timing out (default is
                        600).
        :type timeout: ``int``

        :param max_tries: How many times to retry if a deployment fails before
                          giving up (default is 3).
        :type max_tries: ``int``

        :return: The node object for the new node.
        :rtype:  :class:`VagrantNode`

        """
        task = kwargs["deploy"]
        max_tries = kwargs.get("max_tries", 3)
        ssh_timeout = kwargs.get("ssh_timeout", 10)
        timeout = kwargs.get("timeout", SSH_CONNECT_TIMEOUT)

        node = self.create_node(**kwargs)
        ssh_config = self._vagrant_ssh_config(node.name)

        try:
            _, ip_addresses = self.wait_until_running(
                nodes=[node],
                wait_period=3,
                timeout=kwargs.get("timeout", NODE_ONLINE_WAIT_TIMEOUT),
                ssh_interface=ssh_config["host"])[0]

            self.log.info("Running deployment script on '%s' ..", node.name)
            self._connect_and_run_deployment_script(
                task=task,
                node=node,
                ssh_hostname=ip_addresses[0],
                ssh_port=ssh_config["port"],
                ssh_username=ssh_config["user"],
                ssh_password=None,
                ssh_key_file=ssh_config["key"],
                ssh_timeout=ssh_timeout,
                timeout=timeout,
                max_tries=max_tries)
            self.log.info(".. Finished deployment script on '%s' ..",
                          node.name)
        except Exception as exc:
            raise DeploymentError(node=node, original_exception=exc,
                                  driver=self)
        return node

    def detach_volume(self, volume):
        """Detaches a volume from a node.

        :param volume: Volume to be detached
        :type volume: :class:`VagrantVolume`

        :rtype: ``bool`

        """
        node = volume.attached_to
        if not node:
            return True
        try:
            with self._catalogue as c:
                for n in c.get_nodes():
                    if n.name == node:
                        virtualbox.detach_volume(n.id, volume.path)
                        break
                else:
                    self.log.warn("Volume '%s' attached to node '%s', "
                                  "which does not exist", volume.name, node)
                volume.attached_to = None
                c.update_volume(volume)
                return True
        except:
            self.log.warn("Cannot detach volume %s", volume.name,
                          exc_info=True)
            return False

    def destroy_node(self, node):
        """Destroy a node.

        Volumes attached to this node and networks this node is connected to
        are not destroyed.

        :param node: The node to be destroyed
        :type node: :class:`VagrantNode`

        :return: True if the destroy was successful, False otherwise.
        :rtype: ``bool``

        """
        self.log.info("Destroying node '%s' ..", node.name)
        try:
            with self._catalogue as c:
                self._vagrant("destroy --force", node.name)
                for ip in node._public_ips + node._private_ips:
                    self.log.debug("destroy_node(): Deallocating address %s",
                                   ip)
                    n = c.find_network(ip.network_name)
                    n.deallocate_address(ip.address)
                    c.update_network(n)
                for v in c.get_volumes():
                    if v.attached_to == node.name:
                        self.log.debug("destroy_node(): Detaching %s", v)
                        self.detach_volume(v)
                c.remove_node(node)
            self.log.info(".. Node '%s' destroyed", node.name)
            return True
        except:
            self.log.warn("Cannot destroy %s", node.name, exc_info=True)
            return False

    def destroy_volume(self, volume):
        """Destroys a storage volume.

        :param volume: Volume to be destroyed
        :type volume: :class:`VagrantVolume`

        :return: True if the destroy was successful, False otherwise.
        :rtype: ``bool``

        """
        if volume.attached_to:
            self.log.warn("Cannot destroy volume %s: It is attached to %s",
                          volume.name, volume.attached_to)
            return False
        with self._catalogue as c:
            c.remove_volume(volume)
            try:
                os.unlink(volume.path)
            except OSError:
                self.log.warn("Cannot unlink %s", volume.path, exc_info=True)
        return True

    def get_image(self, image_id):
        """Returns a Vagrant image object.

        :param image_id: Image to retrieve (like ``hashicorp/precise64``).
        :type image_id: ``str``

        :return: Image instance on success.
        :rtype :class:`VagrantImage`

        """
        def find_image():
            for image in self.list_images():
                if image.id == image_id:
                    return image

        image = find_image()
        if image:
            return image

        self.log.info("Fetching image '%s' ..", image_id)
        self._vagrant("box add --provider virtualbox", image_id)
        self.log.info(".. Done fetching image '%s'", image_id)

        return find_image()

    def list_images(self, location=None):
        """Lists registered images

        :return: A list of registered images
        :rtype: ``list`` of :class:`VagrantImage`

        """
        images = []
        cur = None
        for line in self._vagrant("box list").strip().split("\n"):
            self.log.debug("Scanning [%s]", line)
            if not line:
                continue
            bits = line.split(",")
            key = bits[2]
            data = bits[3]
            if key == "box-name":
                if cur is not None:
                    images.append(cur)
                cur = {"box-name": data}
            elif key == "box-provider":
                cur["box-provider"] = data
        if cur:
            images.append(cur)

        return [VagrantImage(name=i["box-name"], driver=self)
                for i in images if i["box-provider"] == "virtualbox"]

    def list_nodes(self):
        """Lists all registered nodes.

        :return:  A list of node objects
        :rtype: ``list`` of :class:`VagrantNode`

        """
        with self._catalogue as catalogue:
            nodes = catalogue.get_nodes()
            self.log.debug("Catalogue nodes: %s", nodes)
            return nodes

    def list_sizes(self, location=None):
        """Returns the single size object defined.

        The default size object instructs ``libcloud`` to create a node with
        the same amount of memory and number of CPUs as those of the Vagrant
        image it is created from.

        The ``location`` argument is ignored.

        :return: A list of one single size object
        :rtype: ``list`` of :class:`VagrantSize`

        """
        return [VagrantNodeSize(name="default",
                                ram=0,
                                driver=self,
                                extra={"cpu": 0})]

    def list_volumes(self):
        """Lists all registered storage volumes.

        :rtype: ``list`` of :class:`VagrantVolume`

        """
        with self._catalogue as c:
            ret = c.get_volumes()
            self.log.debug("list_volumes(): Returning %s", ret)
            return ret

    def reboot_node(self, node):
        """Reboot a node.

        :param node: The node to be rebooted
        :type node: :class:`VagrantNode`

        :return: ``True`` if the reboot was successful, otherwise ``False``
        :rtype: ``bool``

        """
        self.log.info("Rebooting node '%s' ..", node.name)
        with self._catalogue:
            try:
                self._vagrant("reload --no-provision", node.name)
                self.log.info(".. Node '%s' rebooted", node.name)
                return True
            except:
                self.log.debug("Cannot reload %s", node.name, exc_info=True)

    def wait_until_running(self, nodes, wait_period=3, timeout=600,
                           ssh_interface="public_ips", force_ipv4=True):
        """Block until the provided nodes are considered running.

        Unlike its overridden version, this method does not require any public
        or private IP address to be assigned to the host, since Vagrant's NAT
        interface is always available when a node's state is
        ``NodeState.RUNNING``.

        :param nodes: List of nodes to wait for.
        :type nodes: ``list`` of :class:`VagrantNode`

        :param wait_period: How many seconds to wait between each loop
                            iteration. (default is 3)
        :type wait_period: ``int``

        :param timeout: How many seconds to wait before giving up.
                        (default is 600)
        :type timeout: ``int``

        :param ssh_interface: Ignored parameter.
        :type ssh_interface: ``str``

        :param force_ipv4: Ignored parameter
        :type force_ipv4: ``bool``

        :return: ``[(VagrantNode, ip_addresses)]`` list of tuple of
                 VagrantNode instance and list of IP addresses of their
                 Vagrant NAT interfaces.
        :rtype: ``list`` of ``tuple``

        """
        start = time.time()
        end = start + timeout

        uuids = set([node.uuid for node in nodes])

        self.log.debug("wait_until_running(): Waiting for %s (%s)", nodes,
                       uuids)
        while time.time() < end:
            running = [n for n in self.list_nodes()
                       if (n.uuid in uuids and
                           n.state == NodeState.RUNNING)]
            self.log.debug("wait_until_running(): Running nodes: %s", running)
            if len(running) == len(uuids):
                host = self._vagrant_ssh_config(running[0].name)["host"]
                ret = list(zip(running, itertools.repeat([host])))
                self.log.debug("wait_until_running(): Returning %s", ret)
                return ret
            else:
                time.sleep(wait_period)

        raise LibcloudError(value='Timed out after %s seconds' % (timeout,),
                            driver=self)

    def ex_create_network(self, name, cidr, public=False):
        """Creates a Vagrant network.

        This is an extension method.

        :param name: Name of the network
        :type name:  ``str``

        :param cidr: Address and netmask of the network
        :type cidr:  ``str``

        :param public: Whether this is a public or a private network (default:
                       private network)
        :type public"  ``Bool``

        :return: A Vagrant network object
        :rtype:  :class:`VagrantNetwork`

        """
        self.log.debug("ex_create_network(%s, %s, %s): Entering",
                       name, cidr, public)
        with self._catalogue as c:
            network = VagrantNetwork(name, cidr, public,
                                     allocated=[], host_interface=None)
            c.add_network(network)
            return network

    def ex_destroy_network(self, network):
        """Destroys a Vagrant network object.

        Networks with addresses in use by nodes cannot be destroyed.

        This is an extension method.

        :param network: The Vagrant network to destroy
        :type network:  :class:`VagrantNetwork`

        :return: ``True`` on success, ``False`` otherwise
        :rtype:  ``Bool``

        """
        self.log.info("Destroying network '%s' ..", network.name)
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

    def ex_get_node_state(self, node):
        """Returns the state of the given node.

        This is an extension method.

        :param node: The node object
        :type node:  :class:`VagrantNode`

        :rtype: :class:`NodeState`

        """
        try:
            with self._catalogue as c:
                if node.id is None:
                    node_uuid = c.virtualbox_uuid(node)
                else:
                    node_uuid = node.id
                return virtualbox.get_node_state(node_uuid)
        except:
            self.log.warn("Cannot get node state for '%s'", node.name,
                          exc_info=True)
            return NodeState.UNKNOWN

    def ex_list_networks(self):
        """Returns a list of all defined Vagrant networks.

        This is an extension method.

        :rtype: ``list`` of :class:`VagrantNetwork`

        """
        with self._catalogue as c:
            return c.get_networks()

    def ex_ssh_client(self, node):
        """Returns a context manager implementing an SSH client to the given
        node.

        This is an extension method.

        """
        config = self._vagrant_ssh_config(node.name)
        return ssh_client(hostname=config["host"],
                          port=config["port"],
                          username=config["user"],
                          key_files=[config["key"]])

    def ex_start_node(self, node):
        """Starts a node.

        This is an extension method.

        :param node: The node object
        :type node:  :class:`VagrantNode`

        """
        self.log.info("Starting node '%s' ..", node.name)
        self._vagrant("up --provider virtualbox", node.name)
        self.log.info(".. Node '%s' started", node.name)

    def ex_stop_node(self, node):
        """Stops a node.

        This is an extension method.

        :param node: The node object
        :type node:  :class:`VagrantNode`

        """
        self.log.info("Stopping node '%s' ..", node.name)
        with self._catalogue as c:
            if node.id is None:
                node_uuid = c.virtualbox_uuid(node)
            else:
                node_uuid = node.id
            virtualbox.stop_node(node_uuid)
        self.log.info(".. Node '%s' stopped", node.name)

    def _vagrant(self, *args):
        """Executes the ``vagrant`` command in machine-readable output format.

        Raises and error if the exit status is non-zero.

        :param args:  Parameters to ``vagrant``
        :type args:   ``list``

        :return: The combined standard output and standard error of the
                 command.

        :rtype:  ``str``.

        """
        env = dict(os.environ)
        env["VAGRANT_LOG"] = "debug"
        cmdline = ["vagrant --machine-readable"]
        cmdline.extend(args)
        cmdline = " ".join(str(arg) for arg in cmdline)
        self.log.debug("Executing %s (cwd: %s)",
                       cmdline, self._dot_libcloudvagrant)
        p = subprocess.Popen(cmdline, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             env=env,
                             cwd=self._dot_libcloudvagrant)
        stdout, stderr = p.communicate()
        self.log.debug(stdout)
        if p.returncode:
            self.log.warn("%s (cwd: %s) failed: %s",
                          cmdline, self._dot_libcloudvagrant, stderr)
            raise LibcloudError(stdout, driver=self)
        return stdout

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

    def _vagrant_ssh_config(self, node_name):
        ret = {}
        ssh_config = self._vagrant("ssh-config", node_name)
        m = re.search("HostName (.+)$", ssh_config, re.MULTILINE)
        if m:
            ret["host"] = m.group(1)
        m = re.search("User (.+)$", ssh_config, re.MULTILINE)
        if m:
            ret["user"] = m.group(1)
        m = re.search("Port (.+)$", ssh_config, re.MULTILINE)
        if m:
            ret["port"] = int(m.group(1))
        m = re.search("IdentityFile (.+)$", ssh_config, re.MULTILINE)
        if m:
            ret["key"] = m.group(1)
        return ret


@contextmanager
def ssh_client(**kwargs):
    """Context manager that returns an SSH client. The SSH connection is
    opened before entering, and closed before leaving.

    """
    client = SSHClient(**kwargs)
    if not client.connect():
        raise Exception("Cannot create SSH connection with %s" % (client,))
    try:
        yield client
    finally:
        client.close()
