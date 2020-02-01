#!/usr/bin/env bash

set -euo pipefail

# Download Windows binaries from SourceForge
# Kaldi instructions for Windows specifically say to use 32-bit builds, but I couldn't find
# a recent 32-bit build on SourceForge
URL="https://sourceforge.net/projects/openblas/files/v0.2.15/mingw64_dll.zip/download"

MINGW_ROOT="${TRAVIS_BUILD_DIR}/travis/mingw"
(
	echo "Starting MinGW build at $(date)"
	source "$(dirname "$0")/util.sh"

	mkdir -p "$MINGW_ROOT"
	cd "$MINGW_ROOT"

	curl -L --fail -o mingw.zip $URL
	unzip mingw.zip
	rm mingw.zip

	echo "MinGW is installed in ${MINGW_ROOT}"
	find_files_with_ext .dll "$MINGW_ROOT"
) >&2

echo $MINGW_ROOT
