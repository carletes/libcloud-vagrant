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

"""Helper to return the package version."""

import os
import re
import sys


__all__ = [
    "version_string",
]


def version_string():
    """Returns the version string found in ``libcloudvagrant/__init_.py``, or
    ``None`` if it could not be found.

    """
    fname = os.path.join(os.path.dirname(__file__),
                         "libcloudvagrant", "__init__.py")
    with open(fname, "r") as f:
        m = re.search(r'^__version__\s+=\s"(.+?)"', f.read(), re.MULTILINE)
        if m:
            return m.group(1)

if __name__ == "__main__":
    version = version_string()
    if version:
        print version
        rc = 0
    else:
        print >> sys.stderr, "libcloud-vagrant: Cannot determine version"
        rc = 1
    sys.exit(rc)
