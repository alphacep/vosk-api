#!/usr/bin/env bash

set -euo pipefail

# Build OpenFST in travis/openfst
OPENFST_ROOT="${TRAVIS_BUILD_DIR}/travis/openfst"
(
	echo "Starting OpenFST build at $(date)"
	source "$(dirname "$0")/util.sh"

	check_travis_remaining_time_budget 40

	if [[ "${REBUILD_OPENFST:-}" ]]; then
		echo "REBUILD_OPENFST is set. Deleting cached files, if present..."
		rm -rf "$OPENFST_ROOT"
	fi
	if [[ "${BUILD_OPENFST:-}" ]]; then
		echo "BUILD_OPENFST is set. Deleting .valid-cache, if present..."
		rm -f "${OPENFST_ROOT}/.valid-cache"
	fi

	mkdir -p "$OPENFST_ROOT"
	cd "$OPENFST_ROOT"
	if [ -f .valid-cache ]; then
		echo "Reusing cached OpenFST build artifacts: $(cat .valid-cache)"
	else
		if [ -d .git ]; then
			echo "Found cached OpenFST repo. Doing git pull..."
			git pull
		else
			echo "Cloning OpenFST git repo..."
			git clone -b winport --single-branch https://github.com/kkm000/openfst .
			echo "Applying patches..."
			curl https://patch-diff.githubusercontent.com/raw/kkm000/openfst/pull/22.patch | git apply -v
			git apply -v "${TRAVIS_BUILD_DIR}/travis/windows/error-C2371-SSIZE_T-redefinition.patch"
		fi
		if [ ! -d build64 ]; then
			echo "Generating native Makefiles..."
			cmake -S . -B build64 \
				-DCMAKE_TOOLCHAIN_FILE="${TRAVIS_BUILD_DIR}/conan_paths.cmake" \
				-DCMAKE_BUILD_TYPE=Release \
				-DCMAKE_CXX_FLAGS:STRING=" /W0" \
				-DHAVE_FAR=ON \
				-DHAVE_NGRAM=ON \
				-DHAVE_LOOKAHEAD=ON
		fi
		if travis_wait 40 cmake --build build64 --config Release; then
			git describe --always > .valid-cache
			echo "OpenFST build successful: " $(cat .valid-cache)
			echo "Removing intermediate files:"
			find . -type f -name '*.ilk' -or -name '*.obj' -or -name '*.pdb' -ls -delete
		else
			echo "OpenFST build unsuccessful. Keeping intermediate files. Retry the build if it timed out."
		fi
	fi
	find_files_with_ext .lib "$OPENFST_ROOT"
	find_files_with_ext .h "$OPENFST_ROOT"
) >&2

echo $OPENFST_ROOT
