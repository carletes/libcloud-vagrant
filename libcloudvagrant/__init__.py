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

"""A compute provider for Apache Libcloud which uses Vagrant to manage
VirtualBox nodes, networks and volumes.

"""

import os
import re
import subprocess
import sys

from libcloud.compute import providers as compute_providers
from libcloud import security

try:
    import pytest
    PYTEST_FOUND = True
except ImportError:
    PYTEST_FOUND = False

try:
    import netifaces
    NETIFACES_FOUND = True

    # For pyflakes
    netifaces
except ImportError:
    NETIFACES_FOUND = False

from libcloudvagrant.common.types import VAGRANT
from libcloudvagrant.compute import driver as compute_driver


__all__ = [
    "__version__",
    "VAGRANT",
    "test",
]


compute_providers.set_driver(VAGRANT,
                             compute_driver.__name__,
                             compute_driver.VagrantDriver.__name__)

security.CA_CERTS_PATH.append(os.path.join(os.path.dirname(__file__),
                                           "common",
                                           "ca-bundle.crt"))


__version__ = "0.5.0"


def test():  # pragma: no cover
    """Runs the tests for ``libcloud-vagrant``.

    Requires ``nose`` to be installed. The tests take quite a bit of time to
    finish, and use up about 10 GB of disk space and 3 GB of memory, since
    several VMs are created.

    """
    can_run = True
    if not PYTEST_FOUND:
        print >> sys.stderr, "Install 'pytest' in order to run the tests."
        can_run = False

    if not NETIFACES_FOUND:
        print >> sys.stderr, "Install 'netifaces' in order to run the tests."
        can_run = False

    if can_run:
        print "Testing libcloud-vagrant %s" % (__version__,)
        return pytest.main([__name__])


def execute(cmdline):
    p = subprocess.Popen(cmdline,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    stdout, _ = p.communicate()
    if p.returncode:
        raise RuntimeError("Cannot execute '%s': %s", cmdline, stdout)
    return stdout.strip()


def check_versions():
    """Verifies the versions of VirtualBox, Vagrant and the required Vagrant
    plugins.

    """
    vagrant_version = execute("vagrant --version")
    if not vagrant_version.startswith("Vagrant 1.6"):
        raise RuntimeError("Unsupported %s" % (vagrant_version,))

    virtualbox_version = execute("VBoxManage --version")
    if not virtualbox_version.startswith("4.3"):
        raise RuntimeError("Unsupported VirtualBox %s" %
                           (virtualbox_version,))

    vagrant_plugins = execute("vagrant plugin list")
    m = re.search(r"vagrant-libcloud-helper \((.+?)\)", vagrant_plugins)
    if not m:
        print >> sys.stderr, "Installing plugin 'vagrant-libcloud-helper'"
        execute("vagrant plugin update vagrant-libcloud-helper")
    else:
        required = "0.0.2"
        if m.group(1) != required:
            print >> sys.stderr, "Updating plugin 'vagrant-libcloud-helper'"
            execute("vagrant plugin update vagrant-libcloud-helper")


check_versions()
