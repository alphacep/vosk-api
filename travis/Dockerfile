# see https://github.com/dockcross/dockcross
ARG DOCKCROSS_IMAGE=manylinux2010-x64

FROM dockcross/${DOCKCROSS_IMAGE}

# git ref to clone from https://github.com/alphacep/kaldi
ARG KALDI_TAG=lookahead

# git ref to clone from https://github.com/xianyi/OpenBLAS
ARG OPENBLAS_TAG=v0.3.7

# see https://github.com/xianyi/OpenBLAS/blob/develop/TargetList.txt
ARG OPENBLAS_TARGET=NEHALEM

WORKDIR /opt/OpenBLAS
RUN git clone -b "${OPENBLAS_TAG}" --single-branch https://github.com/xianyi/OpenBLAS . \
	&& make -j $(nproc) PREFIX=$(pwd)/install TARGET="${OPENBLAS_TARGET}" USE_LOCKING=1 USE_THREAD=0 HOSTCC=gcc all install \
	# remove intermediate build files to keep image size reasonable
	&& find -name "*.o" -exec rm {} \;

WORKDIR /opt/kaldi
RUN git clone -b "${KALDI_TAG}" --single-branch https://github.com/alphacep/kaldi . \
	&& cd /opt/kaldi/tools \
	&& ln -s /opt/OpenBLAS . \
	&& sed -i 's:status=0:exit 0:g' extras/check_dependencies.sh \
	&& make -j $(nproc) openfst \
	&& cd /opt/kaldi/src \
	&& sed -i "s:TARGET_ARCH=\"\`uname -m\`\":TARGET_ARCH=$(echo $CROSS_TRIPLE|cut -d - -f 1):g" configure \
	&& ./configure --mathlib=OPENBLAS --shared --static-fst=yes --use-cuda=no \
	&& make -j $(nproc) online2 \
	# remove intermediate build files to keep image size reasonable
	&& find /opt/kaldi -type f -name '*.o' -exec rm {} \;

WORKDIR /opt/swig
COPY install-swig-dependencies.sh .
RUN ./install-swig-dependencies.sh

RUN wget --no-check-certificate -O - https://sourceforge.net/projects/swig/files/swig/swig-4.0.1/swig-4.0.1.tar.gz/download \
	| tar xz --strip-components=1 \
	&& ./configure --prefix=/usr --with-python3=/opt/python/cp37-cp37m/bin/python3 \
	&& make -j $(nproc) \
	&& make install \
	&& rm -rf /opt/swig

WORKDIR /io
