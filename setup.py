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

import os
import sys

# XXX Consider ``test_suite = 'nose.collector'`` for testing

from setuptools import find_packages, setup

from version import version_string


def read_requirements():
    ret = []
    fname = os.path.join(os.path.dirname(__file__), "requirements.txt")
    with open(fname, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                ret.append(line)
    return ret


def read_long_description():
    with open("README.rst", "r") as f:
        return f.read()


setup(
    name="libcloud-vagrant",
    version=version_string(),
    description="A libcloud compute provider for local Vagrant boxes",
    long_description=read_long_description(),
    url="https://github.com/carletes/libcloud-vagrant",
    author="Carlos Valiente",
    author_email="carlos@pepelabs.net",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],

    package_dir={
        "libcloudvagrant": "libcloudvagrant",
    },
    packages=find_packages(),
    package_data={
        "libcloudvagrant": ["ca-bundle.crt"],
        "libcloudvagrant.templates": ["Vagrantfile"],
    },
    entry_points={
        "console_scripts": [
            "libcloud-vagrant = libcloudvagrant.cmd:main",
        ],
    },
    install_requires=read_requirements(),

    zip_safe=False,
)
