#!/usr/bin/env bash

set -euo pipefail

# Download Windows binaries from SourceForge
# Kaldi instructions for Windows specifically say to use 32-bit builds, but I couldn't find
# a recent 32-bit build on SourceForge
URL="https://sourceforge.net/projects/openblas/files/v0.3.7/OpenBLAS-0.3.7-x64.zip/download"

OPENBLAS_ROOT="${TRAVIS_BUILD_DIR}/travis/openblas"
(
	echo "Starting OpenBLAS build at $(date)"
	source "$(dirname "$0")/util.sh"

	mkdir -p "$OPENBLAS_ROOT"
	cd "$OPENBLAS_ROOT"
	curl -L --fail -o openblas.zip $URL
	unzip openblas.zip
	rm openblas.zip

	echo "OpenBLAS is installed in ${OPENBLAS_ROOT}"
	find_files_with_ext .lib "$OPENBLAS_ROOT"
	find_files_with_ext .h "$OPENBLAS_ROOT"
) >&2

echo $OPENBLAS_ROOT
