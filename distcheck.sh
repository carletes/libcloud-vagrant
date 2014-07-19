#!/bin/sh

set -x

here="$(cd $(dirname $0) && pwd)"

version=$(python "$here/version.py")

dist_tgz="$here/dist/libcloud-vagrant-${version}.tar.gz"
if [ ! -r "$dist_tgz" ] ; then
  echo "$dist_tgz: Not found"
  exit 1
fi

virtualenv_name="distcheck/libcloud-vagrant-${version}"

rm -rf  $virtualenv_name
virtualenv $virtualenv_name
$virtualenv_name/bin/pip install "$dist_tgz"
$virtualenv_name/bin/pip install -r "$here/requirements-devel.txt"

set +e
$virtualenv_name/bin/python -c "import libcloudvagrant; libcloudvagrant.test()"
rc="$?"
set -e

exit $rc
