# "source" this file rather than executing it directly

travis_wait() {
	shift
	local cmd=("${@}")
	"${cmd[@]}"
}

cmake() {
	echo "Pretending to run cmake ${@}"
}
