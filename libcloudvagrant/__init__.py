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
import sys

from libcloud.compute import providers
from libcloud import security

try:
    import nose
    NOSE_FOUND = True
except ImportError:
    NOSE_FOUND = False

try:
    import netifaces
    NETIFACES_FOUND = True

    # For pyflakes
    netifaces
except ImportError:
    NETIFACES_FOUND = False

from libcloudvagrant.driver import VAGRANT, VagrantDriver, __name__ as pkg_name


__all__ = [
    "__version__",
    "test",
]


providers.set_driver(VAGRANT, pkg_name, VagrantDriver.__name__)

security.CA_CERTS_PATH.append(os.path.join(os.path.dirname(__file__),
                                           "ca-bundle.crt"))


__version__ = "0.4.0"


def test():
    """Runs the tests for ``libcloud-vagrant``.

    Requires ``nose`` to be installed. The tests take quite a bit of time to
    finish, and use up about 10 GB of disk space and 3 GB of memory, since
    several VMs are created.

    """
    can_run = True
    if not NOSE_FOUND:
        print >> sys.stderr, "Install 'nose' in order to run the tests."
        can_run = False

    if not NETIFACES_FOUND:
        print >> sys.stderr, "Install 'netifaces' in order to run the tests."
        can_run = False

    if can_run:
        print "Testing libcloud-vagrant %s" % (__version__,)
        return nose.run(__name__)
