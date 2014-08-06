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

"""A catalogue of Vagrant nodes, networks and volumes."""

import copy
import json
import logging
import os
import pprint
import pwd
import traceback

import ipaddr
import lockfile

from libcloud.common.types import LibcloudError

from libcloudvagrant import templates
from libcloudvagrant.types import (
    VagrantAddress,
    VagrantNetwork,
    VagrantNode,
    VagrantVolume,
)


__all__ = [
    "VagrantCatalogue",
]


_HOME = pwd.getpwuid(os.getuid()).pw_dir


class VagrantCatalogue(object):

    log = logging.getLogger("libcloudvagrant")

    def __init__(self, dname, driver):
        self.dname = dname
        if not os.access(self.dname, os.F_OK):
            os.mkdir(self.dname)
        self.driver = driver
        self._objects = None
        self._previous_objects = None
        self._save_needed = False
        self._lock = lockfile.FileLock(self._catalogue_json)
        self._unlock_on_exit = not self._lock.i_am_locking()

    def __enter__(self):
        self._lock.acquire()
        if os.access(self._catalogue_json, os.R_OK):
            try:
                with open(self._catalogue_json, "rt") as f:
                    self._objects = json.load(f)
                    self.log.debug("Loaded objects: %s",
                                   pprint.pformat(self._objects))
            except:
                try:
                    self._lock.release()
                except:
                    pass
                raise
        else:
            self._objects = {}
            self._save_needed = True
        for k in ("networks", "nodes", "volumes"):
            self._objects.setdefault(k, {})
        self._previous_objects = copy.deepcopy(self._objects)

        return self

    def __exit__(self, *exc_info):
        if any(exc_info):
            self.log.debug("Reverting because of: %s",
                           "".join(traceback.format_exception(*exc_info)))
            self._objects = self._previous_objects

        try:
            if self._save_needed:
                self.save()
        finally:
            if self._unlock_on_exit:
                self._lock.release()

        self._objects = self._previous_objects = None

    def add_network(self, network):
        self.log.debug("add_network(%s): Entering", network)
        params = network.to_dict()
        name = params["name"]
        if name in self._networks:
            n = self._networks[name]
            self.log.debug("add_network(%s): Found existing network %s",
                           network, n)
            for k in ("cidr", "public"):
                if params[k] != n[k]:
                    raise LibcloudError("Network '%s' already defined" %
                                        (name,), driver=self.driver)
            self.log.debug("add_network(%s): Nothing to do", network)
            return

        network_obj = ipaddr.IPNetwork(params["cidr"])
        for n in self._networks.values():
            if network_obj.overlaps(ipaddr.IPNetwork(n["cidr"])):
                raise LibcloudError("Network '%s' overlaps with '%s'" %
                                    (name, n["name"]), driver=self.driver)

        self.log.debug("add_network(%s): Adding", network)
        self._networks[name] = params
        self._save_needed = True

    def add_node(self, node):
        self.log.debug("add_node(): Adding %s", node)
        self._nodes[node.name] = node.to_dict()
        self._save_needed = True

    def add_volume(self, volume):
        self.log.debug("add_volume(): Adding %s", volume)
        self._volumes[volume.name] = volume.to_dict()
        self._save_needed = True

    def find_network(self, network_name):
        try:
            p = self._networks[network_name]
        except KeyError:
            raise LibcloudError("Unknown network '%s'" % (network_name,),
                                driver=self.driver)
        return VagrantNetwork.from_dict(**p)

    def get_networks(self):
        ret = [VagrantNetwork.from_dict(**p) for p in self._networks.values()]
        self.log.debug("get_networks(): Returning %s", ret)
        return ret

    def get_nodes(self):
        return [VagrantNode.from_dict(driver=self.driver, **p)
                for p in self._nodes.values()]

    def get_volumes(self):
        return [VagrantVolume.from_dict(driver=self.driver, **p)
                for p in self._volumes.values()]

    def remove_network(self, network):
        self.log.debug("remove_network(%s): Entering", network)
        try:
            n = self._networks[network.name]
        except KeyError:
            self.log.debug("remove_network(%s): No such network, leaving",
                           network)
            return
        self.log.debug("remove_network(%s): Network: %s", network, n)
        if n["allocated"]:
            raise LibcloudError("Network %s in use" % (network,),
                                driver=self.driver)
        del self._networks[network.name]
        self._save_needed = True

    def remove_node(self, node):
        try:
            del self._nodes[node.name]
        except KeyError:
            pass
        else:
            self._save_needed = True

    def remove_volume(self, volume):
        try:
            del self._volumes[volume.name]
        except KeyError:
            pass
        else:
            self._save_needed = True

    def update_network(self, network):
        params = network.to_dict()
        if not self._networks.get(network.name) == params:
            self._networks[network.name] = params
            self._save_needed = True

    def update_volume(self, volume):
        params = volume.to_dict()
        if not self._volumes[volume.name] == params:
            self._volumes[volume.name] = params
            self._save_needed = True

    def virtualbox_uuid(self, node):
        try:
            node_name = node.name
        except AttributeError:
            node_name = node
        fname = os.path.join(self.dname, ".vagrant/machines", node_name,
                             "virtualbox/id")
        with open(fname, "r") as f:
            return f.read().strip()

    def volume_path(self, volume_name):
        dname = os.path.join(self.dname, "volumes")
        if not os.access(dname, os.F_OK):
            os.mkdir(dname)
        return os.path.join(dname, volume_name)

    def save(self):
        if not self._save_needed:
            return

        self._save_needed = False
        fname = os.path.join(self.dname, "Vagrantfile")
        try:
            params = {
                "gui_enabled": False,
                "nodes": []
            }
            for n in self._nodes.values():
                node = dict(n)
                node["public_ips"] = [self._address_details(ip)
                                      for ip in n["public_ips"]]
                node["private_ips"] = [self._address_details(ip)
                                       for ip in n["private_ips"]]
                params["nodes"].append(node)
            templates.render("Vagrantfile", params, fname)
        except:
            self.log.warn("Error creating %s", fname, exc_info=True)
        fname = self._catalogue_json
        try:
            with open(fname, "w") as f:
                self.log.debug("Saving catalogue %s: %s", fname, self._objects)
                json.dump(self._objects, f, indent=2)
        except:
            self.log.warn("Error creating %s", fname, exc_info=True)

    def _address_details(self, ip):
        ip = VagrantAddress.from_dict(**ip).address
        for name in self._networks:
            n = VagrantNetwork.from_dict(**self._networks[name]).cidr
            if ip in n:
                return {
                    "network": name, "ip": str(ip), "netmask": str(n.netmask),
                }
        raise LibcloudError("No network defined for %s" % (ip,),
                            driver=self.driver)

    @property
    def _networks(self):
        return self._objects["networks"]

    @property
    def _nodes(self):
        return self._objects["nodes"]

    @property
    def _volumes(self):
        return self._objects["volumes"]

    @property
    def _catalogue_json(self):
        return os.path.join(self.dname, "catalogue.json")
