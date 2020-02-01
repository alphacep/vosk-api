# "source" this file rather than executing it directly

check_travis_remaining_time_budget() {
	if [[ ! "${TRAVIS_WILL_KILL_BUILD_AT:-}" ]]; then
		echo "Unable to check remaining time budget since TRAVIS_WILL_KILL_BUILD_AT is not set"
		return 1
	fi
	local now_s=$(date +%s)
	local remaining_s=$(($TRAVIS_WILL_KILL_BUILD_AT - $now_s))
	local minimum_s=$(( $1 * 60 ))
    if [ $remaining_s -lt $minimum_s ]; then
		echo "Travis CI will kill this build in ${remaining_s} seconds, less than required minimum of ${minimum_s}"
		return 2
	fi
}

find_files_with_ext() {
    echo "Listing ${1} files in ${2}:"
    find "$2" -type f -name "*${1}"
}

if [ -f "${HOME}/.travis/functions" ]; then
	source "${HOME}/.travis/functions"
else
	source "$(dirname $0)/fake.sh"
fi
