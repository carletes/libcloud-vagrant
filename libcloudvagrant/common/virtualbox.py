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

"""Virtualbox-related code."""

import logging
import re
import subprocess

from libcloud.common.types import LibcloudError
from libcloud.compute.types import NodeState


__all__ = [
    "attach_volume",
    "create_volume",
    "destroy_host_interface",
    "detach_volume",
    "get_host_interfaces",
    "get_node_state",
    "stop_node",
]


LOG = logging.getLogger("liibcloudvagrant")


def attach_volume(node_uuid, volume_path, device):
    controller, device, port = find_sata_slot(node_uuid, device)
    vboxmanage("storageattach", node_uuid,
               "--storagectl", '"%s"' % (controller,),
               "--port", port,
               "--device", device,
               "--type hdd",
               "--medium", volume_path)


def create_volume(path, size):
    return vboxmanage("createhd",
                      "--size", size,
                      "--format VDI",
                      "--filename", path)


def destroy_host_interface(ifname):
    return vboxmanage("hostonlyif remove", ifname)


_VOLUME_RE_TEMPL = r'"(.+?)-(\d+)-(\d)"="(%s)"'


def detach_volume(node_uuid, volume_path):
    frag = vboxmanage("showvminfo", node_uuid, "--details --machinereadable")
    m = re.search(_VOLUME_RE_TEMPL % (re.escape(volume_path),), frag)
    if m:
        controller, device, port = m.group(1), m.group(3), m.group(2)
        vboxmanage("storageattach", node_uuid,
                   "--storagectl", '"%s"' % (controller,),
                   "--port", port,
                   "--device", device,
                   "--type hdd",
                   "--medium none")


_HOST_IFACES_RE = re.compile(r'^hostonlyadapter(\d+)="(.+?)"$')


def get_host_interfaces(node_uuid):
    ret = []
    frag = vboxmanage("showvminfo", node_uuid, "--details --machinereadable")
    for line in frag.splitlines():
        m = _HOST_IFACES_RE.search(line)
        if m:
            ret.append((m.group(1), m.group(2)))
    LOG.debug("get_host_interfaces(%s): %s", node_uuid, ret)
    return [iface for (_, iface) in sorted(ret)]


_NODE_STATE_RE = re.compile(r'VMState="(.+?)"')

_NODE_STATES = {
    # From ``src/VBox/Frontends/VBoxManage/VBoxManageInfo.cpp`` under
    # https://www.virtualbox.org/browser/vbox/trunk/
    "aborted": NodeState.STOPPED,
    "deletingsnapshot": NodeState.PENDING,
    "deletingsnapshotlive": NodeState.RUNNING,
    "deletingsnapshotlivepaused": NodeState.PENDING,
    "gurumeditation": NodeState.STOPPED,
    "livesnapshotting": NodeState.RUNNING,
    "paused": NodeState.STOPPED,
    "poweroff": NodeState.STOPPED,
    "restoring": NodeState.PENDING,
    "restoringsnapshot": NodeState.PENDING,
    "running": NodeState.RUNNING,
    "saved": NodeState.RUNNING,
    "saving": NodeState.PENDING,
    "settingup": NodeState.PENDING,
    "starting": NodeState.PENDING,
    "stopping": NodeState.RUNNING,
    "teleported": NodeState.RUNNING,
    "teleporting": NodeState.PENDING,
    "teleportingin": NodeState.PENDING,
    "teleportingpausedvm": NodeState.PENDING,
}


def get_node_state(node_uuid):
    frag = vboxmanage("showvminfo", node_uuid, "--details --machinereadable")
    m = _NODE_STATE_RE.search(frag, re.MULTILINE)
    if m:
        ret = m.group(1)
    else:
        ret = None

    LOG.debug("get_node_state(%s): VirtualBox reported %s", node_uuid, ret)
    ret = _NODE_STATES.get(ret, NodeState.UNKNOWN)
    LOG.debug("get_node_state(%s): Returning %s", node_uuid, ret)
    return ret


def stop_node(node_uuid):
    return vboxmanage("controlvm", node_uuid, "poweroff")


_CONTROLLER_RE = re.compile(r'^storagecontroller([a-z]+)(\d+)="(.+)"$')


def find_sata_controllers(frag):
    ret = {}
    entries = {}
    for line in frag.split("\n"):
        m = _CONTROLLER_RE.search(line)
        if not m:
            continue
        k, n, v = m.group(1), m.group(2), m.group(3)
        c = entries.setdefault(n, {})
        c[k] = v

    for c in entries.values():
        ret.setdefault(c["type"], []).append(c["name"])
    return ret.get("IntelAhci", [])


_DEVICE_RE = re.compile(r"/dev/sd([a-z])")

_DEVICE_RE_TEMPL = r'^"%s-%d-%d"="(.+?)"$'


def find_sata_slot(node_uuid, device):
    frag = vboxmanage("showvminfo", node_uuid, "--details --machinereadable")
    available = []
    for c in find_sata_controllers(frag):
        LOG.debug("Examining controller %s", c)
        dev = 0
        for p in xrange(30):
            m = re.search(_DEVICE_RE_TEMPL % (c, p, dev),
                          frag, re.MULTILINE)
            if m and m.group(1) != "none":
                LOG.debug("Slot '%s-%s-%s' busy (%s)",
                          c, p, dev, m.group(1))
            else:
                LOG.debug("Slot '%s-%s-%s' available", c, p, dev)
                available.append(p)

        LOG.debug("Available ports: %s", available)
        if not available:
            raise LibcloudError("No storage controller slots available")

        if device is None:
            port = available[0]
            LOG.debug("Returning '%s-%s-%s'", c, dev, port)
            return c, dev, port

        m = re.search(_DEVICE_RE, device)
        if not m:
            raise LibcloudError("Invalid SATA device '%s'" % (device,))
        port = ord(m.group(1)) - ord('a')
        LOG.debug("Requested port for %s: %s", device, port)
        if port not in available:
            raise LibcloudError("Device %s already in use" % (device,))

        LOG.debug("Returning '%s-%s-%s'", c, dev, port)
        return c, dev, port


def vboxmanage(*args):
    cmdline = ["VBoxManage -q"]
    cmdline.extend(args)
    cmdline = " ".join(str(arg) for arg in cmdline)
    LOG.debug("Executing %s", cmdline)
    p = subprocess.Popen(cmdline, shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    stdout, _ = p.communicate()
    if p.returncode or "VBoxManage: error" in stdout:
        raise LibcloudError(stdout)
    LOG.debug(stdout)
    return stdout
