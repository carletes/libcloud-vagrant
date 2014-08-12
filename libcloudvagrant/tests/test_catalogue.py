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

"""Unit tests for catalogues."""

import os
import json

from libcloudvagrant.common.catalogue import VagrantCatalogue


__all__ = [
    "test_catalogue_files",
    "test_objects",
]


# XXX Write tests to explore the effects of corrupted internal data, write
# errors when saving ``catalogue.json`` and ``Vagrantfile``, ...


def test_catalogue_files(tmpdir, driver):
    """Vagrant contexts create both a ``VagrantFile`` and a
    ``catalogue.json``.

    """
    dname = tmpdir.strpath
    # XXX Ensure that things still work if do an ``rmdir(dname)`` here, before
    # entering the context manager.
    with VagrantCatalogue(dname, driver):
        for f in ("Vagrantfile", "catalogue.json"):
            fname = os.path.join(dname, f)
            assert not os.access(fname, os.F_OK), "Unexpected '%s'" % (fname,)

    for f in ("Vagrantfile", "catalogue.json"):
        fname = os.path.join(dname, f)
        assert os.access(fname, os.F_OK), "Missing '%s'" % (fname,)


SAMPLE_CATALOGUE = {
    "nodes": {
        "nginx": {
            "id": "b236a285-4337-4e1a-82be-98ff9f9d31b3",
            "name": "nginx",
            "public_ips": [{"address": "10.0.0.1", "network_name": "pub"}],
            "private_ips": [{"address": "172.16.0.1", "network_name": "priv"}],
            "size": {
                "name": "default",
                "ram": 0,
                "cpus": 1,
            },
            "image": {
                "name": "ubuntu/trusty64",
            },
            "allocate_sata_ports": 30,
        },
    },
    "networks": {
        "pub": {
            "name": "pub",
            "cidr": "10.0.0.0/8",
            "public": True,
            "allocated": ["10.0.0.1"],
            "host_interface": "vboxnet2",
        },
        "priv": {
            "name": "priv",
            "cidr": "172.16.0.0/16",
            "public": True,
            "allocated": ["172.16.0.1"],
            "host_interface": None,
        },
    },
    "volumes": {
        "data-web": {
            "name": "data-web",
            "size": 50,
            "attached_to": "nginx",
            "path": "/data/data-web.vdi",
        },
        "logs-web": {
            "name": "logs-web",
            "size": 50,
            "attached_to": "nginx",
            "path": "/data/logs-web.vdi",
        },
    }
}


def test_objects(tmpdir, driver):
    """Keep track of the canonical JSON representation of the catalogue.

    """
    dname = tmpdir.strpath
    with open(os.path.join(dname, "catalogue.json"), "w") as f:
        json.dump(SAMPLE_CATALOGUE, f)

    with VagrantCatalogue(dname, driver) as c:
        assert (SAMPLE_CATALOGUE["networks"].values() ==
                [n.to_dict() for n in c.get_networks()])
        assert (SAMPLE_CATALOGUE["nodes"].values() ==
                [n.to_dict() for n in c.get_nodes()])
        assert (SAMPLE_CATALOGUE["volumes"].values() ==
                [v.to_dict() for v in c.get_volumes()])
