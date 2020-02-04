#!/usr/bin/env bash

set -xeuo pipefail

# To build SWIG, we need to get some libraries and headers. In particular, we need to have
# Python headers and libraries to link against.
#
# dockcross/manylinux* images are based on CentOS, and come with several Python environments,
# such as /opt/python/cp37-cp37m/bin/python3
#
# dockcross/linux-arm* images are based on Debian, and do not come with Python 3
#
# Neither type of image has the PCRE library required for building SWIG

build_python() {
	git_tag=$1
	two_digit_version=$(echo "${git_tag}" | sed -e 's:[^0-9]::g' | head -c 2)
	prefix="/opt/python/cp${two_digit_version}-cp${two_digit_version}m"
	tmpdir=$(mktemp -d)
	cd $tmpdir
	wget https://github.com/python/cpython/archive/${git_tag}.zip
	unzip *.zip
	cd */
	./configure --prefix="$prefix"
	make -j $(nproc)
	make install
	cd /
	rm -rf $tmpdir
}

build_deb_src() {
	pkg=$1; shift
	extra_config="$*"
	tmpdir=$(mktemp -d)
	cd $tmpdir
	apt-get source $pkg
	cd */
	./configure --prefix=$CROSS_ROOT $extra_config
	make -j $(nproc)
	make install
	cd /
	rm -rf $tmpdir
}

build_libssl() {
	tmpdir=$(mktemp -d)
	cd $tmpdir
	apt-get source libssl-dev
	cd */
	CROSS_COMPILE= MACHINE="${CROSS_TRIPLE/-*/}" ./config --prefix=$CROSS_ROOT
	make -j $(nproc)
	make install
	cd /
	rm -rf $tmpdir
}

export LDFLAGS="-L${CROSS_ROOT}/lib"
export CFLAGS="-I${CROSS_ROOT}/include"
export CPPFLAGS="${CFLAGS}"

if [[ $DEFAULT_DOCKCROSS_IMAGE == *manylinux* ]]; then
	yum -y update
	yum -y install pcre-devel
else
	awk '/deb / {print $0; sub(/^deb /, "deb-src ", $0); print $0}' /etc/apt/sources.list > sources.list.mod
	mv sources.list.mod /etc/apt/sources.list
	apt-get update
	apt-get install -y --no-install-recommends unzip
	build_deb_src zlib1g
	build_deb_src libpcre3 --enable-shared=no
	build_deb_src libffi --host=$CROSS_TRIPLE
	build_libssl
	build_python v3.7.6
fi
