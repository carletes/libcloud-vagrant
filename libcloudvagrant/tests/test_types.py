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

"""Unit tests for data types."""

from libcloudvagrant.tests import new_driver
from libcloudvagrant.types import (
    VagrantAddress,
    VagrantImage,
    VagrantNetwork,
    VagrantNode,
    VagrantNodeSize,
    VagrantVolume,
)


__all__ = [
    "test_serializable",
    "test_serializable_with_driver",
]


driver = new_driver()


def test_serializable():
    """Serializable types can be converted to and from their dict
    representations.

    """
    assert_serializable(VagrantAddress,
                        {"address": "10.0.0.1", "network_name": "net1"})
    assert_serializable(VagrantNetwork,
                        {
                            "name": "net1",
                            "cidr": "10.0.0.0/8",
                            "public": True,
                            "allocated": [],
                            "host_interface": "vboxnet4",
                        },
                        {
                            "name": "net1",
                            "cidr": "10.0.0.0/8",
                            "public": True,
                            "allocated": [
                                "10.0.0.1",
                                "10.0.0.2",
                            ],
                            "host_interface": None,
                        })


def test_serializable_with_driver():
    """Serializable types can be converted to and from their dict
    representations.

    """
    assert_serializable_with_driver(VagrantImage,
                                    {
                                        "name": "ubuntu/trusty64",
                                    })
    assert_serializable_with_driver(VagrantNode,
                                    {
                                        "id": "27036b03-13a1-45d6-9030-a3faef699ba9",
                                        "name": "node1",
                                        "public_ips": [],
                                        "private_ips": [],
                                        "size": {
                                            "name": "default",
                                            "ram": 4096,
                                            "cpus": 3,
                                        },
                                        "image": {"name": "ubuntu/trusty64"},
                                    },
                                    {
                                        "id": "361f2550-bc23-4eca-ad22-49914dd8b530",
                                        "name": "node1",
                                        "public_ips": [
                                            {
                                                "address": "10.0.0.1",
                                                "network_name": "pub",
                                            },
                                        ],
                                        "private_ips": [
                                            {
                                                "address": "172.16.0.1",
                                                "network_name": "priv",
                                            },
                                        ],
                                        "size": {
                                            "name": "default",
                                            "ram": 1024,
                                            "cpus": 2,
                                        },
                                        "image": {"name": "ubuntu/trusty64"},
                                    })
    assert_serializable_with_driver(VagrantNodeSize,
                                    {
                                        "name": "default",
                                        "ram": 2048,
                                        "cpus": 2,
                                    })
    assert_serializable_with_driver(VagrantVolume,
                                    {
                                        "name": "test-volume",
                                        "size": 42,
                                        "attached_to": None,
                                        "path": "/data/test-volume.vdi",
                                    },
                                    {
                                        "name": "test-volume",
                                        "size": 42,
                                        "attached_to": "node1",
                                        "path": "/data/test-volume.vdi",
                                    })


def assert_serializable(cls, *params):
    """Serializable types can be converted to and from their dict
    representations.

    """
    for p in params:
        obj = cls.from_dict(**p)
        serialized = obj.to_dict()
        assert serialized == p
        recreated = cls.from_dict(**serialized)
        assert recreated == obj


def assert_serializable_with_driver(cls, *params):
    """Serializable types can be converted to and from their dict
    representations.

    """
    for p in params:
        obj = cls.from_dict(driver=driver, **p)
        serialized = obj.to_dict()
        assert serialized == p
        recreated = cls.from_dict(driver=driver, **serialized)
        assert recreated == obj
