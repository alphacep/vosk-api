#!/usr/bin/env bash

set -euo pipefail

# Build Kaldi in travis/kaldi
KALDI_ROOT="${TRAVIS_BUILD_DIR}/travis/kaldi"

win_path() {
	# '/c/foo' -> 'c:/foo'
	echo $1 | sed -e 's~^/\([a-z]\)/~\1:/~i'
}

find_sln() {
	find "$KALDI_ROOT" -type f -name '*.sln'
}

(
	echo "Starting Kaldi build at $(date)"
	source "$(dirname "$0")/util.sh"

	check_travis_remaining_time_budget 40

	if [[ "${REBUILD_KALDI:-}" ]]; then
		echo "REBUILD_KALDI is set. Deleting cached files, if present..."
		rm -rf "$KALDI_ROOT"
	fi
	if [[ "${BUILD_KALDI:-}" ]]; then
		echo "BUILD_KALDI is set. Deleting .valid-cache, if present..."
		rm -f "${KALDI_ROOT}/.valid-cache"
	fi

	mkdir -p "$KALDI_ROOT"
	cd "$KALDI_ROOT"
	if [ -f .valid-cache ]; then
		echo "Reusing cached Kaldi build artifacts: $(cat .valid-cache)"
	else
		if [ -d .git ]; then
			echo "Found cached Kaldi repo. Doing git pull..."
			git pull
		else
			echo "Cloning Kaldi git repo..."
			git clone -b lookahead --single-branch https://github.com/alphacep/kaldi .
		fi
		
		cd windows
		
		if [ ! -f kaldiwin.props ]; then
			cp kaldiwin_openblas.props kaldiwin.props
		fi
		echo "Listing $(readlink -f kaldiwin.props):"
		cat kaldiwin.props
		
		if [ ! -f variables.props ]; then
			cp variables.props.dev variables.props
			sed -ie "s~<OPENBLASDIR>.*</OPENBLASDIR>~<OPENBLASDIR>$(win_path "$OPENBLAS_ROOT")</OPENBLASDIR>~" variables.props
			sed -ie "s~<OPENFST>.*</OPENFST>~<OPENFST>$(win_path "$OPENFST_ROOT")</OPENFST>~" variables.props
			sed -ie "s~<OPENFSTLIB>.*</OPENFSTLIB>~<OPENFSTLIB>$(win_path "${OPENFST_ROOT}/build64")</OPENFSTLIB>~" variables.props
		fi
		echo "Listing $(readlink -f variables.props):"
		cat variables.props

		SLN="$(find_sln)"
		if [ ! -f "$SLN" ]; then
			echo "Generating MSBuild Solution..."
			./generate_solution.pl --vsver vs2017 --enable-openblas
			./get_version.pl
			SLN="$(find_sln)"
		else
			echo "Re-using existing MSBuild Solution"
		fi
		echo "Listing projects in MSBuild Solution: ${SLN}"
		grep Project "$SLN"
		
		cd "$KALDI_ROOT"
		if travis_wait 40 '/c/Program Files (x86)/Microsoft Visual Studio/2017/BuildTools/MSBuild/15.0/Bin/MSBuild.exe' \
			"$(win_path "$SLN")" \
			-consoleloggerparameters:ErrorsOnly \
			-maxcpucount \
			-property:Configuration=Release \
			-property:Platform=x64 \
			-target:kaldi-online2 \
			-target:kaldi-decoder \
			-target:kaldi-ivector \
			-target:kaldi-gmm \
			-target:kaldi-nnet3 \
			-target:kaldi-tree \
			-target:kaldi-feat \
			-target:kaldi-lat \
			-target:kaldi-hmm \
			-target:kaldi-transform \
			-target:kaldi-cudamatrix \
			-target:kaldi-matrix \
			-target:kaldi-fstext \
			-target:kaldi-util \
			-target:kaldi-base
		then
			git describe --always > .valid-cache
			echo "Kaldi build successful: " $(cat .valid-cache)
			echo "Removing intermediate files:"
			find . -type f -name '*.ilk' -or -name '*.obj' -or -name '*.pdb' -ls -delete
		else
			echo "Kaldi build unsuccessful. Keeping intermediate files. Retry the build if it timed out."
		fi
	fi
	find_files_with_ext .lib "$KALDI_ROOT"
	find_files_with_ext .h "$KALDI_ROOT"
) >&2

echo $KALDI_ROOT
