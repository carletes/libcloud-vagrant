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

"""Unit tests from ``libcloud``."""

import unittest

from libcloud.test import compute

from libcloudvagrant.tests import new_driver, sample_node


__all__ = [
    "ComputeTestCase",
]


class ComputeTestCase(unittest.TestCase, compute.TestCaseMixin):

    """Tests defined in ``libcloud.test.compute.TestCaseMixin``."""

    should_list_locations = False
    should_list_volumes = True

    driver = new_driver()

    def test_reboot_node_response(self):
        with sample_node():
            super(ComputeTestCase, self).test_reboot_node_response()

    def test_list_nodes_response(self):
        with sample_node():
            super(ComputeTestCase, self).test_list_nodes_response()
