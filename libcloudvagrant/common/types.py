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

"""Data types common to all Vagrant drivers."""

__all__ = [
    "VAGRANT",
    "Serializable",
]


# Type string for the compute provider.
VAGRANT = "vagrant"


class Serializable(object):

    """Objects with dict represantations, suitable for JSON or YAML
    serialization.

    """

    @classmethod
    def from_dict(cls, **params):
        """Builds an instance based on its dict representation.

        """
        return cls(**params)

    def to_dict(self):
        """Returns this object's dict representation/

        """
        raise NotImplementedError()

    def __eq__(self, other):
        try:
            return self.to_dict() == other.to_dict()
        except AttributeError:
            return False

    def __repr__(self):
        cls = self.__class__.__name__
        fields = ("%s=%s" % (k, v) for (k, v) in self.to_dict().items())
        return "%s(%s)" % (cls, " ".join(fields))
