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

"""A command-line tool for libcloud-vagrant."""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
import textwrap

from libcloud.compute.providers import get_driver

from libcloudvagrant.driver import VAGRANT


__all__ = [
    "main",
]


LOG = logging.getLogger("libcloudvagrant")


def destroy(driver):
    """Destroys all nodes, networks and volumes in your Vagrant environment.

    """
    ok = True
    for n in driver.list_nodes():
        try:
            driver.destroy_node(n)
        except:
            LOG.warn("Cannot destroy node '%s'", n.name, exc_info=True)
            ok = False

    for network in driver.ex_list_networks():
        try:
            driver.ex_destroy_network(network)
        except:
            LOG.warn("Cannot destroy network '%s'", n.name, exc_info=True)
            ok = False

    return ok


def list_objects(driver):
    """Lists all nodes, networks and volumes in your Vagrant environment.

    """
    networks = driver.ex_list_networks()
    if not networks:
        print "No networks"
    else:
        print underlined("Networks")
        for n in networks:
            public = (n.public and
                      "(public, host address: %s)" % (n.host_address,) or "")
            print "%-10s %-16s %s" % (n.name, n.cidr, public)
        print

    nodes = driver.list_nodes()
    if not nodes:
        print "No nodes"
    else:
        print underlined("Nodes")
        for n in nodes:
            addrs = ", ".join(n.public_ips + n.private_ips)
            size = n.size
            cpus = size.extra.get("cpus", "unknown")
            print "%-20s %3s CPU %6d RAM  %s" % (n.name, cpus, size.ram, addrs)
        print

    volumes = driver.list_volumes()
    if not volumes:
        print "No volumes"
    else:
        print underlined("Volumes")
        for v in volumes:
            owner = v.extra.get("attached_to")
            owner = owner and "(attached to %s)" % (owner,) or ""
            print "%-20s  %4d GB  %s" % (v.name, v.size, owner)
        print


def screen(driver):
    """Opens a screen(1) session to all nodes in your Vagrant environment.

    """
    nodes = driver.list_nodes()
    if not nodes:
        LOG.info("No nodes defined")
        return

    fd, screenrc = tempfile.mkstemp(prefix="cloud-")
    for node in nodes:
        ssh = driver._vagrant_ssh_config(node.name)
        ssh["opts"] = " ".join([
            "-o 'StrictHostKeyChecking no'",
            "-o 'UserKnownHostsFile /dev/null'",
        ])
        ssh = "ssh -p %(port)s -i %(key)s %(opts)s %(user)s@%(host)s" % ssh
        os.write(fd, "screen -t %s %s\n" % (node.name, ssh))
    os.write(fd, "select 0\n")
    p = subprocess.Popen("screen -S libcloud-vagrant -DR -c %s" % (screenrc,),
                         shell=True)
    rc = p.wait()
    os.close(fd)
    os.unlink(screenrc)
    return rc


def underlined(msg, ch="-"):
    return "\n".join((msg, ch * len(msg)))


COMMANDS = {
    "destroy": destroy,
    "list": list_objects,
    "screen": screen,
}


def main():
    """Manage your Vagrant libcloud environment.

    """
    formatter_class = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(prog="libcloud-vagrant",
                                description=main.__doc__.strip(),
                                epilog=format_help(),
                                formatter_class=formatter_class)
    p.add_argument("command", metavar="<cmd>", type=str, choices=COMMANDS,
                   help="command to execute")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(message)s")
    driver = get_driver(VAGRANT)()
    return COMMANDS[args.command](driver)


def format_help():
    """Help for libcloud-vagrant commands.

    Available commands:

        destroy
            %(destroy)s

        list
            %(list)s

        screen
            %(screen)s

    """
    msg = (format_help.__doc__.strip() %
           dict((k, v.__doc__) for (k, v) in COMMANDS.items()))
    lines = msg.splitlines()
    return textwrap.dedent("\n".join(lines[2:]))


if __name__ == "__main__":
    sys.exit(main())
